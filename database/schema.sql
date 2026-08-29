-- =============================================================================
-- Invoice Error Detector — MySQL 8.0 database schema
--   Phase 2: database foundation
--   Phase 2.1: hardening (company/invoice duplicate index, confidence_score,
--              upload_batches lifecycle)
--   Phase 4: rule-based validation engine ('Critical' invoice status; new
--              rule validation types: NEGATIVE_AMOUNT, QUANTITY_INVALID,
--              UNIT_PRICE_INVALID, GST_OUT_OF_RANGE, EMPTY_PRODUCT_NAME)
--   Phase 5: duplicate detection intelligence (DUPLICATE_EXACT, DUPLICATE_VENDOR,
--              DUPLICATE_NEAR, DUPLICATE_DATE, DUPLICATE_ITEM validation types;
--              confidence_score stores the deterministic match confidence)
-- -----------------------------------------------------------------------------
-- Engine  : InnoDB (ACID + FK enforcement)   Charset: utf8mb4 / utf8mb4_unicode_ci
-- Future  : duplicate detection, tax / GST validation, price-anomaly detection,
--           risk scoring, payment reconciliation — all query the same tables.
--
-- Re-running is safe: existing tables are dropped and recreated.
-- =============================================================================

SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS invoice_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE invoice_db;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS validation_results;
DROP TABLE IF EXISTS invoice_items;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS upload_batches;
DROP TABLE IF EXISTS vendors;
DROP TABLE IF EXISTS companies;
SET FOREIGN_KEY_CHECKS = 1;

-- -----------------------------------------------------------------------------
-- 1. companies : the single company that PAYS invoices (tenant / "who pays")
-- -----------------------------------------------------------------------------
CREATE TABLE companies (
    company_id   INT          NOT NULL AUTO_INCREMENT,
    company_name VARCHAR(255) NOT NULL,
    gst_number   CHAR(15)     NOT NULL,                -- 15-char Indian GSTIN
    email        VARCHAR(255) NOT NULL,
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (company_id),
    UNIQUE KEY uk_companies_gst   (gst_number),
    UNIQUE KEY uk_companies_email (email),
    CONSTRAINT chk_companies_gst_format
        CHECK (gst_number REGEXP '^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$')
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. vendors : suppliers the company procures from
-- -----------------------------------------------------------------------------
CREATE TABLE vendors (
    vendor_id   INT          NOT NULL AUTO_INCREMENT,
    company_id  INT          NOT NULL,
    vendor_name VARCHAR(255) NOT NULL,
    gst_number  CHAR(15)     NULL,                     -- NULL allowed for foreign/unregistered
    email       VARCHAR(255) NULL,
    phone       VARCHAR(20)  NULL,
    status      ENUM('Active', 'Inactive', 'Blacklisted')
                             NOT NULL DEFAULT 'Active',
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (vendor_id),
    UNIQUE KEY uk_vendors_company_gst (company_id, gst_number),  -- NULLs pass as duplicate-free
    KEY idx_vendors_company (company_id),
    KEY idx_vendors_status  (status),
    CONSTRAINT fk_vendors_company
        FOREIGN KEY (company_id) REFERENCES companies (company_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    -- optional soft integrity: vendor email must look like an email
    CONSTRAINT chk_vendors_email
        CHECK (email IS NULL OR email REGEXP '^[^@]+@[^@]+\\.[^@]+$'),
    CONSTRAINT chk_vendors_gst_format
        CHECK (gst_number IS NULL OR gst_number REGEXP '^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$')
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3. upload_batches : tracking log for (bulk) file upload job runs
-- -----------------------------------------------------------------------------
CREATE TABLE upload_batches (
    batch_id           INT          NOT NULL AUTO_INCREMENT,
    file_name          VARCHAR(255) NOT NULL,
    uploaded_by        VARCHAR(64)  NOT NULL,
    uploaded_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_invoices     INT          NOT NULL DEFAULT 0,
    processed_invoices INT          NOT NULL DEFAULT 0,
    failed_invoices    INT          NOT NULL DEFAULT 0,
    status             ENUM('Processing', 'Completed', 'Failed')
                                    NOT NULL DEFAULT 'Processing',
    created_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                         ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (batch_id),
    KEY idx_batches_status    (status),
    KEY idx_batches_uploader  (uploaded_by, uploaded_at),
    CONSTRAINT chk_batches_counts_non_negative
        CHECK (total_invoices >= 0 AND processed_invoices >= 0 AND failed_invoices >= 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 4. invoices : header record per vendor invoice received
-- -----------------------------------------------------------------------------
CREATE TABLE invoices (
    invoice_id     INT          NOT NULL AUTO_INCREMENT,
    company_id     INT          NOT NULL,
    vendor_id      INT          NOT NULL,
    invoice_number VARCHAR(64)  NOT NULL,              -- vendor's reference number
    batch_id       INT          NULL,                  -- bulk-upload batch that created it
    invoice_date   DATE         NOT NULL,
    subtotal       DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    tax_amount     DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    total_amount   DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    status         ENUM('Pending', 'Valid', 'Needs Review',
                        'High Risk', 'Critical', 'Duplicate', 'Paid')
                               NOT NULL DEFAULT 'Pending',
    risk_score     DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (invoice_id),
    KEY idx_invoices_company  (company_id),
    KEY idx_invoices_vendor   (vendor_id),
    KEY idx_invoices_batch    (batch_id),
    KEY idx_company_invoice   (company_id, invoice_number),  -- company-wise duplicate lookup
    KEY idx_invoices_number   (invoice_number, company_id),  -- number-first duplicate lookup
    KEY idx_invoices_date     (invoice_date),
    KEY idx_invoices_status   (status),
    KEY idx_invoices_risk     (risk_score),
    CONSTRAINT fk_invoices_company
        FOREIGN KEY (company_id) REFERENCES companies (company_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_invoices_vendor
        FOREIGN KEY (vendor_id) REFERENCES vendors (vendor_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_invoices_batch
        FOREIGN KEY (batch_id) REFERENCES upload_batches (batch_id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    -- monetary sanity / business rules
    CONSTRAINT chk_invoices_amounts_non_negative
        CHECK (subtotal >= 0 AND tax_amount >= 0 AND total_amount >= 0),
    CONSTRAINT chk_invoices_total_consistency
        CHECK (ABS((subtotal + tax_amount) - total_amount) <= 0.01),
    CONSTRAINT chk_invoices_risk_range
        CHECK (risk_score BETWEEN 0 AND 100)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 5. invoice_items : line items belonging to an invoice
-- -----------------------------------------------------------------------------
CREATE TABLE invoice_items (
    item_id      INT          NOT NULL AUTO_INCREMENT,
    invoice_id   INT          NOT NULL,
    product_name VARCHAR(255) NOT NULL DEFAULT 'General',
    quantity     DECIMAL(12,3) NOT NULL,
    unit_price   DECIMAL(14,2) NOT NULL,
    tax_percent  DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    line_total   DECIMAL(14,2) NOT NULL,               -- qty*uprice*(1+tax%) stored for speed
    PRIMARY KEY (item_id),
    KEY idx_items_invoice (invoice_id),
    KEY idx_items_product (product_name),
    CONSTRAINT fk_items_invoice
        FOREIGN KEY (invoice_id) REFERENCES invoices (invoice_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT chk_items_non_negative
        CHECK (quantity >= 0 AND unit_price >= 0 AND line_total >= 0),
    CONSTRAINT chk_items_tax_range
        CHECK (tax_percent BETWEEN 0 AND 100)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 6. validation_results : audit trail of every check flag raised per invoice
-- -----------------------------------------------------------------------------
CREATE TABLE validation_results (
    validation_id   INT          NOT NULL AUTO_INCREMENT,
    invoice_id      INT          NOT NULL,
    validation_type VARCHAR(50)  NOT NULL,
    severity        ENUM('INFO', 'WARNING', 'ERROR', 'CRITICAL')
                               NOT NULL DEFAULT 'WARNING',
    message         VARCHAR(500) NOT NULL,
    confidence_score DECIMAL(5,2) DEFAULT NULL,       -- ML confidence 0–100, optional
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (validation_id),
    KEY idx_validation_invoice (invoice_id),
    KEY idx_validation_type   (validation_type),
    CONSTRAINT fk_validation_invoice
        FOREIGN KEY (invoice_id) REFERENCES invoices (invoice_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT chk_validation_type
        CHECK (validation_type IN (
            'DUPLICATE', 'TOTAL_MISMATCH', 'GST_MISMATCH', 'MISSING_FIELD',
            'PRICE_OUTLIER', 'FUTURE_DATE', 'INVALID_DATE', 'RISK_ANOMALY',
            'RECONCILIATION', 'NEGATIVE_AMOUNT', 'QUANTITY_INVALID',
            'UNIT_PRICE_INVALID', 'GST_OUT_OF_RANGE', 'EMPTY_PRODUCT_NAME',
            'DUPLICATE_EXACT', 'DUPLICATE_VENDOR', 'DUPLICATE_NEAR',
            'DUPLICATE_DATE', 'DUPLICATE_ITEM'
        ))
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;