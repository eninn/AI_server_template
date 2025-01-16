import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

class S3Client:
    def __init__(self, bucket_name, aws_access_key=None, aws_secret_key=None, region_name='us-east-1'):
        """
        S3Client 초기화. 인증 정보가 제공되지 않으면 기본 AWS 설정을 사용.
        """
        self.bucket_name = bucket_name
        try:
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=region_name
            )
        except NoCredentialsError:
            raise Exception("AWS 자격 증명을 찾을 수 없습니다.")
        except PartialCredentialsError:
            raise Exception("AWS 자격 증명이 불완전합니다.")

    def upload_file(self, file_path, object_name=None):
        """
        S3 버킷에 파일 업로드.
        """
        if object_name is None:
            object_name = file_path.split('/')[-1]  # 기본적으로 파일 이름을 S3 키로 사용

        try:
            self.s3.upload_file(file_path, self.bucket_name, object_name)
            print(f"파일 업로드 성공: {object_name}")
            return True
        except FileNotFoundError:
            print("파일을 찾을 수 없습니다.")
        except ClientError as e:
            print(f"클라이언트 에러 발생: {e}")
        return False

    def download_file(self, object_name, file_path):
        """
        S3 버킷에서 파일 다운로드.
        """
        try:
            self.s3.download_file(self.bucket_name, object_name, file_path)
            print(f"파일 다운로드 성공: {file_path}")
            return True
        except FileNotFoundError:
            print("저장 경로가 올바르지 않습니다.")
        except ClientError as e:
            print(f"클라이언트 에러 발생: {e}")
        return False

    def list_files(self, prefix=''):
        """
        S3 버킷 내 파일 목록 가져오기.
        """
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]
                print(f"파일 목록: {files}")
                return files
            else:
                print("파일이 없습니다.")
                return []
        except ClientError as e:
            print(f"클라이언트 에러 발생: {e}")
            return []

# 사용 예제
if __name__ == "__main__":
    BUCKET_NAME = 'your-s3-bucket-name'

    s3_client = S3Client(
        bucket_name=BUCKET_NAME,
        aws_access_key='your-access-key',
        aws_secret_key='your-secret-key',
        region_name='us-east-1'
    )

    # 파일 업로드
    s3_client.upload_file('local_path/to_file.txt', 's3_key/remote_file.txt')

    # 파일 다운로드
    s3_client.download_file('s3_key/remote_file.txt', 'local_path/to_save_file.txt')

    # 파일 목록 조회
    s3_client.list_files('s3_key/')
