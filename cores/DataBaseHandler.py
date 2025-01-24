import os
import sqlite3
from datetime import datetime

class DBHandler:
    def __init__(self, db_path: str, file_root_path: str, maximum_disk_size: int = 5 * 1024 * 1024 * 1024):
        self.db_path = db_path
        self.file_root_path = file_root_path
        self.max_total_size = maximum_disk_size

    def init_db(self, reset: bool = False):
        """
        데이터베이스 초기화
        :param reset: True일 경우 기존 데이터베이스 파일을 삭제하고 새로 생성.
        """
        if reset and os.path.exists(self.db_path):
            os.remove(self.db_path)
            print(f"기존 데이터베이스 파일 삭제: {self.db_path}")

        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reference_voice_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL UNIQUE,
            last_used DATETIME NOT NULL,
            file_size INTEGER
        )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS file_name_idx ON reference_voice_files (file_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS last_used_idx ON reference_voice_files (last_used)")
        self.conn.commit()

        # 파일 루트 경로에 있는 파일들 등록
        self.register_existing_files()

        self.conn.close()

    def register_existing_files(self):
        """
        file_root_path에 있는 모든 파일을 데이터베이스에 등록.
        """        
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # 루트 경로의 모든 파일 탐색
        for root, _, files in os.walk(self.file_root_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                # 이미 등록된 파일인지 확인
                cursor.execute("SELECT id FROM reference_voice_files WHERE file_name = ?", (file,))
                if cursor.fetchone() is None:
                    now = datetime.now()
                    # 파일 등록
                    cursor.execute("""
                    INSERT INTO reference_voice_files (file_name, last_used, file_size)
                    VALUES (?, ?, ?)
                    """, (file, now, file_size))
                    # print(f"파일 등록 완료: {file}, 크기: {file_size} bytes")

        self.conn.commit()
        self.conn.close()

    def check_and_update_file(self, file_name: str) -> bool:
        """
        파일 경로를 확인하고, 데이터베이스에 존재 여부와 상태를 업데이트.
        
        :param file_name: 확인할 파일 이름.
        :return: 파일이 존재하면 True, 존재하지 않으면 False
        """
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # 현재 시간 가져오기
        now = datetime.now()

        # DB에서 파일 존재 여부 확인
        cursor.execute("SELECT id FROM reference_voice_files WHERE file_name = ?", (file_name,))
        result = cursor.fetchone()

        if result:
            # 파일이 이미 존재하면 last_used 업데이트
            cursor.execute("UPDATE reference_voice_files SET last_used = ? WHERE file_name = ?", (now, file_name))
            self.conn.commit()
            # print(f"파일 업데이트 완료: {file_name}")
            self.conn.close()
            # 파일 경로 반환
            return os.path.join(self.file_root_path, file_name)
        else:
            # 파일이 존재하지 않으면 False 반환
            # print(f"파일이 데이터베이스에 존재하지 않습니다: {file_name}")
            self.conn.close()
            return False

    def register_file(self, file_name: str):
        """
        파일을 데이터베이스에 등록하고, 전체 크기가 임계치를 초과하면 오래된 파일 삭제.

        :param file_name: 등록할 파일 명
        """
        file_path = os.path.join(self.file_root_path, file_name)
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # 파일 크기 및 현재 시간 가져오기
        now = datetime.now()
        file_size = os.path.getsize(file_path)

        # 파일이 이미 존재하는지 확인
        cursor.execute("SELECT id FROM reference_voice_files WHERE file_name = ?", (file_name,))
        result = cursor.fetchone()

        if result:
            # 파일이 존재할 경우 last_used, file_size 업데이트
            cursor.execute("""
            UPDATE reference_voice_files 
            SET last_used = ?, file_size = ? 
            WHERE file_name = ?
            """, (now, file_size, file_name))
            # print(f"파일 업데이트 완료: {file_name}, 크기: {file_size} bytes")
        else:
            # 파일이 존재하지 않을 경우 새로 등록
            cursor.execute("""
            INSERT INTO reference_voice_files (file_name, last_used, file_size)
            VALUES (?, ?, ?)
            """, (file_name, now, file_size))
            # print(f"파일 등록 완료: {file_name}, 크기: {file_size} bytes")

        self.conn.commit()

        # 전체 파일 크기 계산
        cursor.execute("SELECT SUM(file_size) FROM reference_voice_files")
        total_size = cursor.fetchone()[0] or 0

        # 임계치를 초과하는 경우 오래된 파일 삭제
        while total_size > self.max_total_size:
            cursor.execute("""
            SELECT file_name, file_size FROM reference_voice_files 
            ORDER BY last_used ASC LIMIT 1
            """)
            oldest_file = cursor.fetchone()

            if oldest_file:
                oldest_file_name, oldest_file_size = oldest_file

                # 실제 파일 삭제
                oldest_file_path = os.path.join(self.file_root_path, oldest_file_name)
                if os.path.exists(oldest_file_path):
                    os.remove(oldest_file_path)
                    # print(f"오래된 파일 삭제: {oldest_file_path}")

                # 데이터베이스에서 파일 정보 삭제
                cursor.execute("DELETE FROM reference_voice_files WHERE file_name = ?", (oldest_file_name,))
                self.conn.commit()

                # 총 크기 업데이트
                total_size -= oldest_file_size

        self.conn.close()

    def delete_file(self, file_name: str) -> bool:
        """
        파일 이름을 입력받아 데이터베이스와 실제 경로에서 삭제.
        
        :param file_name: 삭제할 파일 이름
        :return: 성공적으로 삭제되면 True, 파일이 없으면 False
        """
        file_path = os.path.join(self.file_root_path, file_name)
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # 파일 존재 여부 확인
        cursor.execute("SELECT id FROM reference_voice_files WHERE file_name = ?", (file_name,))
        result = cursor.fetchone()

        if result:
            # 실제 파일 삭제
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"파일 삭제 완료: {file_path}")

            # 데이터베이스에서 파일 정보 삭제
            cursor.execute("DELETE FROM reference_voice_files WHERE file_name = ?", (file_name,))
            self.conn.commit()
            print(f"데이터베이스에서 파일 정보 삭제 완료: {file_name}")

            self.conn.close()
            return True
        else:
            print(f"파일이 데이터베이스에 존재하지 않습니다: {file_name}")
            self.conn.close()
            return False