# **Database Backup Script**

## 📌 Overview
This script automates database backups using **PostgreSQL’s `pg_dump`** and optionally copies the backup to a NAS drive. The script allows configurable backup intervals, naming conventions, and storage locations.

---

## 📁 Configuration
Modify the `config.conf` file before running the script.

### 🔹 Database Configuration
These settings define how the database backup is created.

| Parameter        | Description                                          | Example Value |
|-----------------|------------------------------------------------------|--------------|
| `PG_DUMP_PATH`  | Path to the `pg_dump` executable                     | `C:\Program Files\PostgreSQL\16\bin\pg_dump` |
| `DB_HOST`       | Database server hostname or IP                        | `localhost` |
| `DB_PORT`       | PostgreSQL database port                              | `5432` |
| `DB_NAME`       | Name of the database to backup                        | `postgres` |
| `DB_USER`       | Database username                                     | `postgres` |
| `DB_PASSWORD`   | Database password                                     | `1234` |
| `BACKUP_DIR`    | Directory where backups are stored                    | `\backups` |

---

### 🔹 NAS Configuration (Optional)
These settings determine whether backups are copied to a network-attached storage (NAS) location.

| Parameter        | Description                                      | Example Value |
|-----------------|--------------------------------------------------|--------------|
| `NAS_PATH`      | Path to NAS storage for backups                   | `Z:\backups` |
| `ENABLE_NAS_COPY` | Enable or disable NAS backup (`True` or `False`) | `False` |

---

### 🔹 Backup Settings
Define how often and in what format backups are stored.

| Parameter         | Description                                      | Example Value |
|------------------|--------------------------------------------------|--------------|
| `backup_interval` | Time between backups (in minutes)               | `30` |
| `BACKUP_MODE`    | `"single"` (all backups in one folder) or `"daily"` (separate folders per day) | `daily` |
| `BACKUP_NAME_FORMAT` | `"detailed"` (timestamped names) or `"daily"` (one backup per day) | `detailed` |

---

## 🚀 How to Use
### 1️⃣ Install PostgreSQL
Ensure PostgreSQL is installed, and `pg_dump` is accessible at the specified `PG_DUMP_PATH`.

### 2️⃣ Configure `config.conf`
Modify the `config.conf` file to match your database and backup preferences.

### 3️⃣ Run the Backup Script
Run the script using:
```sh
python backup_script.py
