// Representative Google Cloud product catalog, grouped by category.
// This is a curated ~65-product set across 12 real GCP categories — not the
// full ~200-product catalog. Swap in the complete list from the data team
// (e.g. via the public products page or `gcloud services list`) without
// touching any component: everything downstream reads from this one file.

export const GCP_PRODUCTS = [
  // Compute
  { name: 'Compute Engine', category: 'Compute' },
  { name: 'App Engine', category: 'Compute' },
  { name: 'Cloud Run', category: 'Compute' },
  { name: 'Google Kubernetes Engine', category: 'Compute' },
  { name: 'Cloud Functions', category: 'Compute' },
  { name: 'Bare Metal Solution', category: 'Compute' },
  { name: 'VMware Engine', category: 'Compute' },
  { name: 'Batch', category: 'Compute' },

  // Storage
  { name: 'Cloud Storage', category: 'Storage' },
  { name: 'Persistent Disk', category: 'Storage' },
  { name: 'Filestore', category: 'Storage' },
  { name: 'Storage Transfer Service', category: 'Storage' },
  { name: 'Transfer Appliance', category: 'Storage' },

  // Databases
  { name: 'Cloud SQL', category: 'Databases' },
  { name: 'Cloud Spanner', category: 'Databases' },
  { name: 'Firestore', category: 'Databases' },
  { name: 'Bigtable', category: 'Databases' },
  { name: 'Memorystore', category: 'Databases' },
  { name: 'AlloyDB', category: 'Databases' },
  { name: 'Database Migration Service', category: 'Databases' },

  // Data Analytics
  { name: 'BigQuery', category: 'Data Analytics' },
  { name: 'Dataflow', category: 'Data Analytics' },
  { name: 'Dataproc', category: 'Data Analytics' },
  { name: 'Pub/Sub', category: 'Data Analytics' },
  { name: 'Cloud Data Fusion', category: 'Data Analytics' },
  { name: 'Cloud Composer', category: 'Data Analytics' },
  { name: 'Looker', category: 'Data Analytics' },
  { name: 'Dataplex', category: 'Data Analytics' },

  // AI & Machine Learning
  { name: 'Vertex AI', category: 'AI & Machine Learning' },
  { name: 'Vertex AI Search', category: 'AI & Machine Learning' },
  { name: 'AutoML', category: 'AI & Machine Learning' },
  { name: 'Natural Language AI', category: 'AI & Machine Learning' },
  { name: 'Vision AI', category: 'AI & Machine Learning' },
  { name: 'Translation AI', category: 'AI & Machine Learning' },
  { name: 'Speech-to-Text', category: 'AI & Machine Learning' },
  { name: 'Text-to-Speech', category: 'AI & Machine Learning' },
  { name: 'Document AI', category: 'AI & Machine Learning' },
  { name: 'Contact Center AI', category: 'AI & Machine Learning' },
  { name: 'Recommendations AI', category: 'AI & Machine Learning' },
  { name: 'Gemini Code Assist', category: 'AI & Machine Learning' },

  // Networking
  { name: 'Virtual Private Cloud', category: 'Networking' },
  { name: 'Cloud Load Balancing', category: 'Networking' },
  { name: 'Cloud CDN', category: 'Networking' },
  { name: 'Cloud DNS', category: 'Networking' },
  { name: 'Cloud Interconnect', category: 'Networking' },
  { name: 'Cloud VPN', category: 'Networking' },
  { name: 'Network Connectivity Center', category: 'Networking' },
  { name: 'Cloud NAT', category: 'Networking' },

  // Security & Identity
  { name: 'Identity and Access Management', category: 'Security & Identity' },
  { name: 'Cloud Identity', category: 'Security & Identity' },
  { name: 'Security Command Center', category: 'Security & Identity' },
  { name: 'Secret Manager', category: 'Security & Identity' },
  { name: 'Cloud KMS', category: 'Security & Identity' },
  { name: 'Chronicle', category: 'Security & Identity' },
  { name: 'BeyondCorp Enterprise', category: 'Security & Identity' },
  { name: 'reCAPTCHA Enterprise', category: 'Security & Identity' },

  // DevOps & Management
  { name: 'Cloud Build', category: 'DevOps & Management' },
  { name: 'Artifact Registry', category: 'DevOps & Management' },
  { name: 'Cloud Deploy', category: 'DevOps & Management' },
  { name: 'Cloud Monitoring', category: 'DevOps & Management' },
  { name: 'Cloud Logging', category: 'DevOps & Management' },
  { name: 'Cloud Trace', category: 'DevOps & Management' },
  { name: 'Error Reporting', category: 'DevOps & Management' },
  { name: 'Cloud Profiler', category: 'DevOps & Management' },

  // Hybrid & Multicloud
  { name: 'Anthos', category: 'Hybrid & Multicloud' },
  { name: 'Google Distributed Cloud', category: 'Hybrid & Multicloud' },
  { name: 'GKE Enterprise', category: 'Hybrid & Multicloud' },

  // Migration
  { name: 'Migrate to Virtual Machines', category: 'Migration' },
  { name: 'Migration Center', category: 'Migration' },

  // Application Integration
  { name: 'Apigee', category: 'Application Integration' },
  { name: 'Cloud Tasks', category: 'Application Integration' },
  { name: 'Cloud Scheduler', category: 'Application Integration' },
  { name: 'Eventarc', category: 'Application Integration' },
  { name: 'Workflows', category: 'Application Integration' },

  // Media & Gaming
  { name: 'Transcoder API', category: 'Media & Gaming' },
  { name: 'Live Stream API', category: 'Media & Gaming' },
  { name: 'Game Servers', category: 'Media & Gaming' },
  { name: 'Immersive Stream for XR', category: 'Media & Gaming' },
];

export const CATEGORIES = [...new Set(GCP_PRODUCTS.map((p) => p.category))];
