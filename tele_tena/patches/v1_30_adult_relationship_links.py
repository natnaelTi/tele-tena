"""Add isolated, consented adult relationship-invitation storage."""
import frappe


def execute():
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_relationship_gate (
        id int PRIMARY KEY
    ) ENGINE=InnoDB''')
    frappe.db.sql('INSERT IGNORE INTO tt_relationship_gate (id) VALUES (1)')
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_relationship_invitation (
        id varchar(36) PRIMARY KEY,
        inviter varchar(140) NOT NULL,
        token_digest char(64) NOT NULL UNIQUE,
        retry_key varchar(80) NOT NULL,
        payload_hash char(64) NOT NULL,
        state varchar(20) NOT NULL,
        consent_version varchar(40) NOT NULL,
        inviter_adult_attested_at datetime(6) NOT NULL,
        created_at datetime(6) NOT NULL,
        expires_at datetime(6) NOT NULL,
        accepted_by varchar(140),
        accepted_at datetime(6),
        relationship_id varchar(36),
        UNIQUE KEY inviter_retry (inviter,retry_key),
        KEY inviter_created (inviter,created_at),
        KEY invite_expiry (state,expires_at)
    ) ENGINE=InnoDB''')
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_relationship_link (
        id varchar(36) PRIMARY KEY,
        participant_a varchar(140) NOT NULL,
        participant_b varchar(140) NOT NULL,
        invitation_id varchar(36) NOT NULL UNIQUE,
        state varchar(20) NOT NULL,
        consent_version varchar(40) NOT NULL,
        consent_a_at datetime(6) NOT NULL,
        consent_b_at datetime(6) NOT NULL,
        created_at datetime(6) NOT NULL,
        ended_at datetime(6),
        ended_by varchar(140),
        KEY relationship_pair (participant_a,participant_b),
        KEY participant_a_state (participant_a,state),
        KEY participant_b_state (participant_b,state)
    ) ENGINE=InnoDB''')
    frappe.db.sql_ddl('''CREATE TABLE IF NOT EXISTS tt_relationship_event (
        id varchar(36) PRIMARY KEY,
        subject_id varchar(36) NOT NULL,
        subject_type varchar(20) NOT NULL,
        actor varchar(140) NOT NULL,
        event_type varchar(24) NOT NULL,
        consent_version varchar(40) NOT NULL,
        created_at datetime(6) NOT NULL,
        KEY relationship_event_time (subject_type,subject_id,created_at)
    ) ENGINE=InnoDB''')
