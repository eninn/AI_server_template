import multiprocessing as mp

from tqdm import tqdm

def small_data_parallel_processing(num_processes:int, func:callable, data_list:list) -> list:
    chunk_size = len(data_list) // num_processes
    chunks = [data_list[i * chunk_size: (i + 1) * chunk_size] for i in range(num_processes)]
    
    if len(data_list) % num_processes != 0:
        chunks[-1].extend(data_list[num_processes * chunk_size:])

    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.map(func, chunks)
    
    flattened_results = [item for sublist in results for item in sublist]
    return flattened_results

def large_data_parallel_processing(num_processes: int, func: callable, data_list: list) -> list:
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = list(tqdm(pool.imap(func, data_list), total=len(data_list), desc="Processing data"))
    
    return results