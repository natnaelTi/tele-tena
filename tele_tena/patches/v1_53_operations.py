"""Additive operational records; no existing data/provider/role changes."""
import json
import frappe
DEFAULTS={'native_events':True,'analytics':False,'errors':False,'replay':False,'archive':False,'alerts':False,'owner':'','alert_email':'','mobile_channel':'Disabled','events_per_day':20000,'event_total_limit':100000,'alert_messages_per_day':100,'errors_per_day':500,'replays_per_day':500,'archive_bytes':1073741824,'recording_bytes':10485760,'export_queue':500,'retry_budget':5,'replay_days':90,'event_days':30,'sample_percent':100,'cooldown_minutes':30,'environment':'review'}
def execute():
 tables={
 'config':'''id INT PRIMARY KEY,revision INT NOT NULL,payload LONGTEXT NOT NULL,modified DATETIME(6) NOT NULL''',
 'preference':'''actor CHAR(64) PRIMARY KEY,analytics TINYINT NOT NULL,replay TINYINT NOT NULL,version VARCHAR(40) NOT NULL,modified DATETIME(6) NOT NULL''',
 'event':'''id CHAR(64) PRIMARY KEY,name VARCHAR(80) NOT NULL,attempt CHAR(64) NOT NULL,actor CHAR(64) NOT NULL,source VARCHAR(10) NOT NULL,role VARCHAR(12) NOT NULL,locale VARCHAR(5) NOT NULL,device VARCHAR(10) NOT NULL,environment VARCHAR(12) NOT NULL,release_id VARCHAR(40) NOT NULL,payment_mode VARCHAR(10) NOT NULL,route VARCHAR(120) NOT NULL,properties TEXT NOT NULL,created DATETIME(6) NOT NULL,aggregated TINYINT NOT NULL DEFAULT 0,delivery VARCHAR(16) NOT NULL DEFAULT 'Pending',tries INT NOT NULL DEFAULT 0,KEY processing(aggregated,created),KEY delivery(delivery,created)''',
 'daily':'''id CHAR(64) PRIMARY KEY,day DATE NOT NULL,name VARCHAR(80) NOT NULL,dimensions TEXT NOT NULL,n BIGINT NOT NULL,KEY period(day,name)''',
 'attempt':'''id CHAR(64) PRIMARY KEY,family VARCHAR(30) NOT NULL,started DATETIME(6) NOT NULL,last_seen DATETIME(6) NOT NULL,state VARCHAR(20) NOT NULL,completed DATETIME(6),dimensions TEXT NOT NULL,KEY period(started,state)''',
 'incident':'''id CHAR(64) PRIMARY KEY,code VARCHAR(80) NOT NULL,severity VARCHAR(12) NOT NULL,state VARCHAR(20) NOT NULL,n INT NOT NULL,first_seen DATETIME(6) NOT NULL,last_seen DATETIME(6) NOT NULL,acknowledged_by VARCHAR(140),acknowledged_at DATETIME(6),last_alert DATETIME(6),recovered DATETIME(6),escalation INT NOT NULL DEFAULT 0''',
 'alert':'''id CHAR(64) PRIMARY KEY,incident CHAR(64) NOT NULL,channel VARCHAR(12) NOT NULL,phase VARCHAR(12) NOT NULL,state VARCHAR(20) NOT NULL,created DATETIME(6) NOT NULL,modified DATETIME(6) NOT NULL''',
 'error':'''id CHAR(36) PRIMARY KEY,fingerprint CHAR(64) NOT NULL,payload TEXT NOT NULL,created DATETIME(6) NOT NULL,state VARCHAR(20) NOT NULL DEFAULT 'Pending',tries INT NOT NULL DEFAULT 0''',
 'support':'''id CHAR(36) PRIMARY KEY,owner VARCHAR(140) NOT NULL,category VARCHAR(30) NOT NULL,description TEXT NOT NULL,followup TINYINT NOT NULL,state VARCHAR(24) NOT NULL,priority VARCHAR(12) NOT NULL,assignee VARCHAR(140),context TEXT NOT NULL,retry_key VARCHAR(100) NOT NULL,digest CHAR(64) NOT NULL,created DATETIME(6) NOT NULL,modified DATETIME(6) NOT NULL,UNIQUE KEY owner_retry(owner,retry_key),KEY state_time(state,modified)''',
 'reply':'''id CHAR(36) PRIMARY KEY,report CHAR(36) NOT NULL,author VARCHAR(140) NOT NULL,audience VARCHAR(10) NOT NULL,body TEXT NOT NULL,retry_key VARCHAR(100) NOT NULL,digest CHAR(64) NOT NULL,created DATETIME(6) NOT NULL,UNIQUE KEY report_retry(report,author,retry_key)''',
 'file':'''id CHAR(36) PRIMARY KEY,report CHAR(36) NOT NULL,filename VARCHAR(200) NOT NULL,mime VARCHAR(30) NOT NULL,sha256 CHAR(64) NOT NULL,size_bytes BIGINT NOT NULL,path CHAR(64) NOT NULL,created DATETIME(6) NOT NULL''',
 'heartbeat':'''name VARCHAR(80) PRIMARY KEY,at DATETIME(6) NOT NULL,details TEXT NOT NULL''',
 'counter':'''day DATE NOT NULL,kind VARCHAR(30) NOT NULL,n BIGINT NOT NULL,PRIMARY KEY(day,kind)''',
 'archive':'''id CHAR(64) PRIMARY KEY,provider_id VARCHAR(100) NOT NULL,captured DATETIME(6) NOT NULL,expires DATETIME(6) NOT NULL,state VARCHAR(20) NOT NULL,size_bytes BIGINT NOT NULL DEFAULT 0,sha256 CHAR(64),format_version VARCHAR(60),player_version VARCHAR(60),object_key CHAR(64),tries INT NOT NULL DEFAULT 0,next_try DATETIME(6),verified DATETIME(6),failure_code VARCHAR(60),modified DATETIME(6) NOT NULL,KEY lifecycle(state,expires)''',
 'deleted':'''id CHAR(64) PRIMARY KEY,deleted DATETIME(6) NOT NULL,reason VARCHAR(30) NOT NULL,provider_state VARCHAR(20) NOT NULL''',
 'report':'''id CHAR(36) PRIMARY KEY,period VARCHAR(7) NOT NULL,version INT NOT NULL,digest CHAR(64) NOT NULL,payload LONGTEXT NOT NULL,annotation TEXT NOT NULL,created DATETIME(6) NOT NULL,UNIQUE KEY period_digest(period,digest)''',
 }
 for name,fields in tables.items():frappe.db.sql_ddl(f'CREATE TABLE IF NOT EXISTS tt_ops_{name} ({fields}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_unicode_ci')
 frappe.db.sql('INSERT IGNORE INTO tt_ops_config VALUES (1,1,%s,UTC_TIMESTAMP(6))',(json.dumps(DEFAULTS),))

 if not frappe.db.sql("SHOW COLUMNS FROM tt_ops_support LIKE 'resolved_at'"):
  frappe.db.sql_ddl("ALTER TABLE tt_ops_support ADD COLUMN resolved_at DATETIME(6)")
