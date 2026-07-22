// Complete GCP Product Catalog categorized for CloudPulse Synthesizer
export const GCP_PRODUCTS = [
  // Compute
  { name: 'Compute Engine', category: 'Compute', description: 'Configurable virtual machines for general-purpose workloads.' },
  { name: 'App Engine', category: 'Compute', description: 'Fully managed platform for building and deploying web apps without managing infrastructure.' },
  { name: 'Cloud Run', category: 'Compute', description: 'Fully managed platform for running stateless containers, scaling automatically to zero.' },
  { name: 'Google Kubernetes Engine', category: 'Compute', description: 'Managed Kubernetes for deploying, managing, and scaling containerized applications.' },
  { name: 'Cloud Run Functions', category: 'Compute', description: 'Event-driven functions that run your code in response to triggers, no server management.' },
  { name: 'Bare Metal Solution', category: 'Compute', description: 'Dedicated bare-metal hardware for specialized enterprise workloads like Oracle databases.' },
  { name: 'VMware Engine', category: 'Compute', description: 'Run VMware workloads natively in Google Cloud without refactoring.' },
  { name: 'Batch', category: 'Compute', description: 'Fully managed service for running batch processing workloads at scale.' },
  { name: 'Cloud TPUs', category: 'Compute', description: 'Custom-built hardware accelerators for training and running machine learning models.' },
  { name: 'Cloud Workstations', category: 'Compute', description: 'Fully managed development environments accessible from a browser.' },
  { name: 'Knative', category: 'Compute', description: 'Open-source platform for building and running serverless containerized applications on Kubernetes.' },

  // Storage
  { name: 'Cloud Storage', category: 'Storage', description: 'Unified object storage for any amount of data, accessible any time.' },
  { name: 'Persistent Disk', category: 'Storage', description: 'Durable block storage for Compute Engine and GKE.' },
  { name: 'Filestore', category: 'Storage', description: 'Fully managed network file storage (NFS) for applications.' },
  { name: 'Storage Transfer Service', category: 'Storage', description: 'Move large volumes of data into and between cloud storage systems.' },
  { name: 'Transfer Appliance', category: 'Storage', description: 'High-capacity physical device for offline bulk data transfer to Google Cloud.' },
  { name: 'Google Cloud NetApp Volumes', category: 'Storage', description: 'Fully managed file storage service built on NetApp\'s ONTAP technology.' },
  { name: 'Backup and Disaster Recovery Service', category: 'Storage', description: 'Centralized backup and recovery management across workloads.' },

  // Databases
  { name: 'Cloud SQL', category: 'Databases', description: 'Fully managed relational database service for MySQL, PostgreSQL, and SQL Server.' },
  { name: 'Cloud Spanner', category: 'Databases', description: 'Globally distributed, strongly consistent relational database.' },
  { name: 'Firestore', category: 'Databases', description: 'Serverless NoSQL document database for web, mobile, and server apps.' },
  { name: 'Cloud Bigtable', category: 'Databases', description: 'Fully managed, scalable NoSQL database for large analytical and operational workloads.' },
  { name: 'Memorystore', category: 'Databases', description: 'Fully managed in-memory data store for Redis and Memcached.' },
  { name: 'AlloyDB', category: 'Databases', description: 'Fully managed PostgreSQL-compatible database built for demanding enterprise workloads.' },
  { name: 'Database Migration Service', category: 'Databases', description: 'Migrate databases to Google Cloud with minimal downtime.' },
  { name: 'Datastream', category: 'Databases', description: 'Serverless change data capture and replication service.' },

  // Data Analytics
  { name: 'BigQuery', category: 'Data Analytics', description: 'Serverless, highly scalable data warehouse with built-in machine learning.' },
  { name: 'Dataflow', category: 'Data Analytics', description: 'Fully managed service for stream and batch data processing.' },
  { name: 'Dataproc', category: 'Data Analytics', description: 'Fully managed Spark and Hadoop service for batch processing, querying, and machine learning.' },
  { name: 'Pub/Sub', category: 'Data Analytics', description: 'Fully managed real-time messaging service for event-driven systems.' },
  { name: 'Cloud Data Fusion', category: 'Data Analytics', description: 'Fully managed, code-free data integration service.' },
  { name: 'Cloud Composer', category: 'Data Analytics', description: 'Fully managed workflow orchestration service built on Apache Airflow.' },
  { name: 'Looker', category: 'Data Analytics', description: 'Enterprise business intelligence and data platform.' },
  { name: 'Looker Studio', category: 'Data Analytics', description: 'Free tool for turning data into customizable, shareable reports and dashboards.' },
  { name: 'Dataplex', category: 'Data Analytics', description: 'Unified data governance and management across distributed data.' },
  { name: 'Dataform', category: 'Data Analytics', description: 'Develop, version, and orchestrate SQL data transformation pipelines in BigQuery.' },
  { name: 'BigQuery Data Transfer Service', category: 'Data Analytics', description: 'Automate data movement from SaaS applications into BigQuery.' },
  { name: 'Earth Engine', category: 'Data Analytics', description: 'Planetary-scale platform for geospatial and environmental data analysis.' },

  // AI & Machine Learning
  { name: 'Vertex AI', category: 'AI & Machine Learning', description: 'Unified platform for building, training, and deploying machine learning models.' },
  { name: 'Vertex AI Studio', category: 'AI & Machine Learning', description: 'Design, test, and customize generative AI prompts and models.' },
  { name: 'Vertex AI Agent Builder', category: 'AI & Machine Learning', description: 'Build and deploy AI agents grounded in your enterprise data.' },
  { name: 'Gemini Enterprise Agent Platform', category: 'AI & Machine Learning', description: 'Platform for building, deploying, and managing enterprise AI agents.' },
  { name: 'Gemini Code Assist', category: 'AI & Machine Learning', description: 'AI-powered coding assistance across the software development lifecycle.' },
  { name: 'AutoML', category: 'AI & Machine Learning', description: 'Train high-quality custom machine learning models with minimal effort.' },
  { name: 'Dialogflow CX', category: 'AI & Machine Learning', description: 'Build advanced conversational AI experiences and virtual agents.' },
  { name: 'Natural Language AI', category: 'AI & Machine Learning', description: 'Extract insights from text using pretrained and custom models.' },
  { name: 'Vision AI', category: 'AI & Machine Learning', description: 'Derive insights from images using pretrained machine learning models.' },
  { name: 'Translation AI', category: 'AI & Machine Learning', description: 'Dynamically translate text across thousands of language pairs.' },
  { name: 'Speech-to-Text', category: 'AI & Machine Learning', description: 'Convert audio to text using powerful speech recognition models.' },
  { name: 'Text-to-Speech', category: 'AI & Machine Learning', description: 'Convert text into natural-sounding speech.' },
  { name: 'Document AI', category: 'AI & Machine Learning', description: 'Extract structured data from documents using machine learning.' },
  { name: 'Contact Center AI', category: 'AI & Machine Learning', description: 'AI-powered virtual agents and insights for customer contact centers.' },
  { name: 'Colab Enterprise', category: 'AI & Machine Learning', description: 'Collaborative, managed notebook environment for data science and ML.' },

  // Networking
  { name: 'Virtual Private Cloud', category: 'Networking', description: 'Global, scalable virtual network for Google Cloud resources.' },
  { name: 'Cloud Load Balancing', category: 'Networking', description: 'Distribute traffic across resources with high performance and reliability.' },
  { name: 'Cloud CDN', category: 'Networking', description: 'Content delivery network for fast, reliable content delivery.' },
  { name: 'Cloud DNS', category: 'Networking', description: 'Scalable, reliable, and managed authoritative Domain Name System service.' },
  { name: 'Cloud Interconnect', category: 'Networking', description: 'Dedicated, high-throughput connectivity between on-premises and Google Cloud.' },
  { name: 'Cloud VPN', category: 'Networking', description: 'Securely connect on-premises networks to Google Cloud over IPsec VPN.' },
  { name: 'Network Connectivity Center', category: 'Networking', description: 'Centralized hub for managing network connectivity across sites and clouds.' },
  { name: 'Cloud NAT', category: 'Networking', description: 'Managed network address translation for outbound connectivity without external IPs.' },
  { name: 'Google Cloud Armor', category: 'Networking', description: 'DDoS protection and web application firewall for applications and services.' },
  { name: 'Cloud Service Mesh', category: 'Networking', description: 'Fully managed service mesh for microservices observability and traffic management.' },

  // Security & Identity
  { name: 'Cloud IAM', category: 'Security & Identity', description: 'Fine-grained access control and visibility for Google Cloud resources.' },
  { name: 'Cloud Identity', category: 'Security & Identity', description: 'Unified identity, access, and endpoint management platform.' },
  { name: 'Security Command Center', category: 'Security & Identity', description: 'Centralized visibility and control for security and risk across Google Cloud.' },
  { name: 'Secret Manager', category: 'Security & Identity', description: 'Securely store, manage, and access API keys, passwords, and other secrets.' },
  { name: 'Cloud Key Management Service', category: 'Security & Identity', description: 'Manage cryptographic keys for your cloud services.' },
  { name: 'Google SecOps', category: 'Security & Identity', description: 'Modernized security operations platform for threat detection and response.' },
  { name: 'BeyondCorp Enterprise', category: 'Security & Identity', description: 'Zero trust solution for secure access without a traditional VPN.' },
  { name: 'reCAPTCHA Enterprise', category: 'Security & Identity', description: 'Protect websites and apps from fraudulent activity and abuse.' },
  { name: 'Access Context Manager', category: 'Security & Identity', description: 'Define fine-grained access levels based on context for zero trust security.' },
  { name: 'Binary Authorization', category: 'Security & Identity', description: 'Deploy-time security control ensuring only trusted container images run.' },
  { name: 'Sensitive Data Protection', category: 'Security & Identity', description: 'Discover, classify, and protect sensitive data across your organization.' }, // Formerly Cloud DLP
  { name: 'Cloud IDS', category: 'Security & Identity', description: 'Cloud-native network threat detection service.' },
  { name: 'Certificate Authority Service', category: 'Security & Identity', description: 'Fully managed private certificate authority for internal PKI.' },
  { name: 'Cloud Asset Inventory', category: 'Security & Identity', description: 'Search, monitor, and analyze all your cloud assets across projects.' },


  // DevOps & Management
  { name: 'Cloud Build', category: 'DevOps & Management', description: 'Fully managed continuous integration and delivery platform.' },
  { name: 'Artifact Registry', category: 'DevOps & Management', description: 'Manage container images and language packages in one place.' },
  { name: 'Cloud Deploy', category: 'DevOps & Management', description: 'Fully managed continuous delivery service for GKE and other runtimes.' },
  { name: 'Cloud Monitoring', category: 'DevOps & Management', description: 'Gain visibility into the performance and health of your applications.' },
  { name: 'Cloud Logging', category: 'DevOps & Management', description: 'Store, search, analyze, and alert on log data at scale.' },
  { name: 'Cloud Trace', category: 'DevOps & Management', description: 'Distributed tracing system for understanding application latency.' },
  { name: 'Error Reporting', category: 'DevOps & Management', description: 'Aggregate and display errors from running cloud services in real time.' },
  { name: 'Cloud Profiler', category: 'DevOps & Management', description: 'Continuous CPU and memory profiling for production applications.' },
  { name: 'Cloud Shell', category: 'DevOps & Management', description: 'Browser-based shell environment for managing Google Cloud resources.' },
  { name: 'Developer Connect', category: 'DevOps & Management', description: 'Connect source code repositories to Google Cloud services and tools.' },
  { name: 'Cloud Billing API', category: 'DevOps & Management', description: 'Programmatically manage and monitor Google Cloud billing accounts.' },
  

  // Hybrid & Multicloud
  { name: 'Anthos', category: 'Hybrid & Multicloud', description: 'Modernize and manage applications consistently across on-premises and multiple clouds.' },
  { name: 'Google Distributed Cloud', category: 'Hybrid & Multicloud', description: 'Run Google Cloud infrastructure and services in your own data center.' },

  // Migration
  { name: 'Migrate to Virtual Machines', category: 'Migration', description: 'Migrate workloads to Compute Engine with minimal downtime.' },
  { name: 'Migration Center', category: 'Migration', description: 'Unified platform to plan, assess, and track cloud migrations.' },

  // Application Integration
  { name: 'Apigee API Management', category: 'Application Integration', description: 'Full lifecycle API management platform for designing and securing APIs.' },
  { name: 'Cloud Tasks', category: 'Application Integration', description: 'Manage execution of distributed, asynchronous tasks.' },
  { name: 'Cloud Scheduler', category: 'Application Integration', description: 'Fully managed cron job scheduler for reliable task automation.' },
  { name: 'Eventarc', category: 'Application Integration', description: 'Route events from sources to targets using a standardized event delivery model.' },
  { name: 'Workflows', category: 'Application Integration', description: 'Orchestrate and automate Google Cloud and API-based services.' },
  { name: 'API Gateway', category: 'Application Integration', description: 'Managed gateway for developing, deploying, and securing APIs.' },
  { name: 'AppSheet', category: 'Application Integration', description: 'No-code platform for building custom applications.' },

  // Media & Gaming
  { name: 'Transcoder API', category: 'Media & Gaming', description: 'Convert video files into formats optimized for different devices and networks.' },
  { name: 'Live Stream API', category: 'Media & Gaming', description: 'Convert live video streams into formats ready for distribution.' },
];

export const CATEGORIES = [...new Set(GCP_PRODUCTS.map((p) => p.category))];