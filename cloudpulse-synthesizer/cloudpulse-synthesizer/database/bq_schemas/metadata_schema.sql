-- CloudPulse document metadata table
-- Replace PROJECT_ID and DATASET_ID before running.

CREATE TABLE IF NOT EXISTS
  `PROJECT_ID.DATASET_ID.document_metadata` (
    document_id STRING NOT NULL,
    title STRING,
    product_name STRING,
    document_type STRING,
    source_url STRING,
    published_date DATE,
    collected_at TIMESTAMP,
    processed_at TIMESTAMP,
    content_hash STRING,
    storage_uri STRING,
    status STRING
  );
