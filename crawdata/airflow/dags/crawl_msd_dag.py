from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

import asyncio
from minio import Minio
import io
import logging
import os

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MinIO config
MINIO_ENDPOINT = 'minio:9000'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioadmin'
BUCKET_NAME = 'crawled-data-medical'

# Path to local link data
FILE_TXT = '/opt/airflow/dags/links_data.txt'  # <-- chỉnh path tuyệt đối

# ========== GET 10 URL ==========
def get_href_task(**context):
    if not os.path.exists(FILE_TXT):
        logger.error(f"❌ File not found: {FILE_TXT}")
        raise FileNotFoundError(f"File not found: {FILE_TXT}")

    with open(FILE_TXT, 'r', encoding='utf-8') as file:
        hrefs = file.readlines()

    if not hrefs:
        logger.warning("⚠️ No links found in file.")
        context['ti'].xcom_push(key='href_list', value=[])
        return

    href_list = [href.strip() for href in hrefs[:10]]
    with open(FILE_TXT, 'w', encoding='utf-8') as file:
        file.writelines(hrefs[10:])

    context['ti'].xcom_push(key='href_list', value=href_list)

# ========== MINIO ==========
def create_minio_client():
    try:
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
        return minio_client
    except Exception as e:
        logger.error(f"MinIO error: {str(e)}")
        raise

# ========== CRAWL ==========
def crawl_pages(**context):
    href_list = context['ti'].xcom_pull(task_ids='get_10_urls', key='href_list')
    if not href_list:
        logger.warning("❌ No URLs received.")
        return False

    try:
        minio_client = create_minio_client()
    except Exception as e:
        return False

    async def async_crawl():
        try:
            async with AsyncWebCrawler() as crawler:
                config = CrawlerRunConfig(
                    cache_mode=CacheMode.ENABLED,
                    pdf=True,
                    semaphore_count=3
                )

                results = await crawler.arun_many(urls=href_list, config=config)

                for idx, result in enumerate(results):
                    if result.pdf:
                        pdf_buffer = io.BytesIO(result.pdf)
                        pdf_size = pdf_buffer.getbuffer().nbytes
                        filename = f"{result.url.replace('https://', '').replace('/', '_')}.pdf"

                        minio_client.put_object(
                            BUCKET_NAME,
                            filename,
                            pdf_buffer,
                            length=pdf_size,
                            content_type='application/pdf'
                        )
                        logger.info(f"✅ Saved {filename} to MinIO.")
            return True
        except Exception as e:
            logger.error(f"❌ Crawl failed: {str(e)}")
            return False

    return asyncio.run(async_crawl())

# ========== DAG ==========
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 3, 27),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='msd_manual_crawler',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=['crawler', 'medical']
) as dag:

    get_urls = PythonOperator(
        task_id='get_10_urls',
        python_callable=get_href_task,
        provide_context=True
    )

    crawl_pages_task = PythonOperator(
        task_id='crawl_and_save',
        python_callable=crawl_pages,
        provide_context=True
    )

    get_urls >> crawl_pages_task
