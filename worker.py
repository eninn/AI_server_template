import os, time, json, requests

from utils.message import send_request_post

job_prior_queue_url = ""
job_queue_url = ""
prod_api_url = ""
test_api_url = ""

complete_api_key = ""

def inference_task(item):
    """
    Input task funtions
    """
    result = {
        "hash": item.hash,
        "is_test": item.is_test,
        "runtime": time.time() - start
    }

    return result


def poll_inf_job_queue():
    while True:
        response = sqs.recevie_message(job_prior_queue_url)
        messages = response.get("Messages", [])
        if messages:
            for message in messages:
                try:
                    receipt_handle = message["ReceiptHandle"]
                    task_body = json.loads(message["Body"])
                    task_item = ItemTextToSpeechWav.model_validate(task_body)
                    result = inference_task(task_item)

                    url = test_api_url if task_item.is_test else prod_api_url
                    send_stts_request_post(url, result, complete_api_key)

                    sqs.delete_message(job_prior_queue_url, receipt_handle)
                    stts_logger.add_info("inference_task", f"Task completed and pushed to completion queue: {result}")
                except Exception as e:
                    stts_logger.add_error("inference_task", f"Error while polling priority job queue: {e}")
                    sqs.delete_message(job_prior_queue_url, receipt_handle)
                    time.sleep(1)  # 에러 발생 시 큐삭제 후 다음작업 수행
            continue            


        response = sqs.recevie_message(job_queue_url)
        messages = response.get("Messages", [])
        if messages:
            for message in messages:
                try:
                    receipt_handle = message["ReceiptHandle"]
                    task_body = json.loads(message["Body"])
                    task_item = ItemTextToSpeechWav.model_validate(task_body)
                    result = inference_task(task_item)

                    url = test_api_url if task_item.is_test else prod_api_url
                    send_stts_request_post(url, result, complete_api_key)

                    sqs.delete_message(job_queue_url, receipt_handle)
                    stts_logger.add_info("inference_task", f"Task completed and pushed to completion queue: {result}")
                except Exception as e:
                    stts_logger.add_error("inference_task", f"Error while polling job queue: {e}")
                    sqs.delete_message(job_queue_url, receipt_handle)
                    time.sleep(1)  # 에러 발생 시 큐삭제 후 다음작업 수행

if __name__ == "__main__":
    print("Starting inference worker...")
    poll_inf_job_queue()