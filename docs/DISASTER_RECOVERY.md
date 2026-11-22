# TalentMatch.ai - Disaster Recovery (DR) & Backup Runbook

## 1. Overview & Service Level Objectives

- **Target System**: TalentMatch.ai Enterprise Recruitment Platform
- **Recovery Time Objective (RTO)**: `< 60 minutes`
- **Recovery Point Objective (RPO)**: `< 24 hours` (daily automated snapshots) or `< 5 minutes` with PostgreSQL WAL archiving.
- **Critical Data Assets**:
  1. PostgreSQL Database (`users`, `jobs`, `candidates`, `resumes`, `matching_analyses`, `shortlists`, `interview_kits`)
  2. Vercel Blob / Cloud Resume Storage (`resumes/*`)
  3. Environment Configuration & Secret Credentials

---

## 2. Automated Backup Strategy

### Daily Database Snapshots
- Script: `scripts/backup_database.py`
- Executed via cron / scheduled job: `0 2 * * * /app/scripts/backup_database.py`
- Formats:
  - Compressed SQL dump (`.sql.gz`) with SHA-256 integrity checksum (`.sha256`).
- Retention Policy:
  - 7 rolling daily snapshots kept locally in `/backups`
  - Automated offsite replication to cloud cold storage (AWS S3 / GCS bucket with server-side encryption enabled).

### Storage & Resume Artifacts
- Resumes stored in **Vercel Blob Store** or **S3-compatible Object Storage**.
- Object versioning enabled to protect against accidental deletions or malicious overwrites.

---

## 3. Disaster Recovery Scenarios & Procedures

### Scenario A: Database Corruption or Data Loss
1. **Identify Corruption Timestamp**:
   - Determine the last known good state prior to the incident.
2. **Retrieve Latest Valid Snapshot**:
   - Locate the latest `.sql.gz` archive in the secure backups directory or cloud cold store.
   - Verify SHA-256 integrity:
     ```bash
     sha256sum -c talentmatch_pg_backup_YYYYMMDD_HHMMSS.sha256
     ```
3. **Restore PostgreSQL Database**:
   ```bash
   gunzip -c talentmatch_pg_backup_YYYYMMDD_HHMMSS.sql.gz | psql -U talentmatch -d talentmatch_prod
   ```
4. **Run Verification Suite**:
   ```bash
   pytest backend/tests/ -v
   curl -f http://localhost:8000/health
   ```

### Scenario B: Cloud Provider / Regional Outage (Vercel / AWS / Neon)
1. **Switch DNS to Standby Environment**:
   - Update Cloudflare / Route53 DNS CNAME to standby container instance or alternate cloud region.
2. **Provision Standby PostgreSQL**:
   - Point `DATABASE_URL` in environment secrets to secondary read-replica or promoted standby instance.
3. **Verify Health Endpoint**:
   ```bash
   curl -I https://backup.talentmatch.ai/health
   ```
4. **Post-Recovery Verification**:
   - Confirm recruiter authentication (`/api/auth/login`).
   - Confirm candidate list rendering and AI match scoring.

---

## 4. Verification & Drill Schedule
- Automated restore drill: executed quarterly on staging environment.
- Checksum audit: performed weekly during scheduled health sweeps.
