// Complete GCP Product Catalog categorized for CloudPulse Synthesizer
export const GCP_PRODUCTS = [
  // Compute
  { name: 'Compute Engine', category: 'Compute' },
  { name: 'App Engine', category: 'Compute' },
  { name: 'Cloud Run', category: 'Compute' },
  { name: 'Google Kubernetes Engine', category: 'Compute' },
  { name: 'Cloud Run Functions', category: 'Compute' },
  { name: 'Bare Metal Solution', category: 'Compute' },
  { name: 'VMware Engine', category: 'Compute' },
  { name: 'Batch', category: 'Compute' },
  { name: 'Cloud TPUs', category: 'Compute' },
  { name: 'Cloud Workstations', category: 'Compute' },

  // Storage
  { name: 'Cloud Storage', category: 'Storage' },
  { name: 'Persistent Disk', category: 'Storage' },
  { name: 'Filestore', category: 'Storage' },
  { name: 'Storage Transfer Service', category: 'Storage' },
  { name: 'Transfer Appliance', category: 'Storage' },
  { name: 'Google Cloud NetApp Volumes', category: 'Storage' },
  { name: 'Backup and Disaster Recovery Service', category: 'Storage' },

  // Databases
  { name: 'Cloud SQL', category: 'Databases' },
  { name: 'Cloud Spanner', category: 'Databases' },
  { name: 'Firestore', category: 'Databases' },
  { name: 'Cloud Bigtable', category: 'Databases' },
  { name: 'Memorystore', category: 'Databases' },
  { name: 'AlloyDB', category: 'Databases' },
  { name: 'Database Migration Service', category: 'Databases' },
  { name: 'Datastream', category: 'Databases' },

  // Data Analytics
  { name: 'BigQuery', category: 'Data Analytics' },
  { name: 'Dataflow', category: 'Data Analytics' },
  { name: 'Dataproc', category: 'Data Analytics' },
  { name: 'Pub/Sub', category: 'Data Analytics' },
  { name: 'Cloud Data Fusion', category: 'Data Analytics' },
  { name: 'Cloud Composer', category: 'Data Analytics' },
  { name: 'Looker', category: 'Data Analytics' },
  { name: 'Looker Studio', category: 'Data Analytics' },
  { name: 'Dataplex', category: 'Data Analytics' },
  { name: 'Dataform', category: 'Data Analytics' },
  { name: 'BigQuery Data Transfer Service', category: 'Data Analytics' },

  // AI & Machine Learning
  { name: 'Vertex AI', category: 'AI & Machine Learning' },
  { name: 'Vertex AI Studio', category: 'AI & Machine Learning' },
  { name: 'Vertex AI Agent Builder', category: 'AI & Machine Learning' },
  { name: 'Gemini Enterprise Agent Platform', category: 'AI & Machine Learning' },
  { name: 'Gemini Code Assist', category: 'AI & Machine Learning' },
  { name: 'AutoML', category: 'AI & Machine Learning' },
  { name: 'Dialogflow CX', category: 'AI & Machine Learning' },
  { name: 'Natural Language AI', category: 'AI & Machine Learning' },
  { name: 'Vision AI', category: 'AI & Machine Learning' },
  { name: 'Translation AI', category: 'AI & Machine Learning' },
  { name: 'Speech-to-Text', category: 'AI & Machine Learning' },
  { name: 'Text-to-Speech', category: 'AI & Machine Learning' },
  { name: 'Document AI', category: 'AI & Machine Learning' },
  { name: 'Contact Center AI', category: 'AI & Machine Learning' },
  { name: 'Colab Enterprise', category: 'AI & Machine Learning' },

  // Networking
  { name: 'Virtual Private Cloud', category: 'Networking' },
  { name: 'Cloud Load Balancing', category: 'Networking' },
  { name: 'Cloud CDN', category: 'Networking' },
  { name: 'Cloud DNS', category: 'Networking' },
  { name: 'Cloud Interconnect', category: 'Networking' },
  { name: 'Cloud VPN', category: 'Networking' },
  { name: 'Network Connectivity Center', category: 'Networking' },
  { name: 'Cloud NAT', category: 'Networking' },
  { name: 'Google Cloud Armor', category: 'Networking' },
  { name: 'Cloud Service Mesh', category: 'Networking' },

  // Security & Identity
  { name: 'Cloud IAM', category: 'Security & Identity' },
  { name: 'Cloud Identity', category: 'Security & Identity' },
  { name: 'Security Command Center', category: 'Security & Identity' },
  { name: 'Secret Manager', category: 'Security & Identity' },
  { name: 'Cloud Key Management Service', category: 'Security & Identity' },
  { name: 'Google SecOps', category: 'Security & Identity' },
  { name: 'BeyondCorp Enterprise', category: 'Security & Identity' },
  { name: 'reCAPTCHA Enterprise', category: 'Security & Identity' },
  { name: 'Access Context Manager', category: 'Security & Identity' },
  { name: 'Binary Authorization', category: 'Security & Identity' },
  { name: 'Sensitive Data Protection', category: 'Security & Identity' }, // Formerly Cloud DLP

  // DevOps & Management
  { name: 'Cloud Build', category: 'DevOps & Management' },
  { name: 'Artifact Registry', category: 'DevOps & Management' },
  { name: 'Cloud Deploy', category: 'DevOps & Management' },
  { name: 'Cloud Monitoring', category: 'DevOps & Management' },
  { name: 'Cloud Logging', category: 'DevOps & Management' },
  { name: 'Cloud Trace', category: 'DevOps & Management' },
  { name: 'Error Reporting', category: 'DevOps & Management' },
  { name: 'Cloud Profiler', category: 'DevOps & Management' },
  { name: 'Cloud Shell', category: 'DevOps & Management' },
  { name: 'Developer Connect', category: 'DevOps & Management' },

  // Hybrid & Multicloud
  { name: 'Anthos', category: 'Hybrid & Multicloud' },
  { name: 'Google Distributed Cloud', category: 'Hybrid & Multicloud' },

  // Migration
  { name: 'Migrate to Virtual Machines', category: 'Migration' },
  { name: 'Migration Center', category: 'Migration' },

  // Application Integration
  { name: 'Apigee API Management', category: 'Application Integration' },
  { name: 'Cloud Tasks', category: 'Application Integration' },
  { name: 'Cloud Scheduler', category: 'Application Integration' },
  { name: 'Eventarc', category: 'Application Integration' },
  { name: 'Workflows', category: 'Application Integration' },
  { name: 'API Gateway', category: 'Application Integration' },
  { name: 'AppSheet', category: 'Application Integration' },

  // Media & Gaming
  { name: 'Transcoder API', category: 'Media & Gaming' },
  { name: 'Live Stream API', category: 'Media & Gaming' },
];

export const CATEGORIES = [...new Set(GCP_PRODUCTS.map((p) => p.category))];