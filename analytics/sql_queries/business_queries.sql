-- =============================================================================
-- Invoice Error Detector — Business Analytics Queries  (Phase 2: database)
-- Target: MySQL 8 (schema in database/schema.sql, data in database/seed_data.sql)
-- =============================================================================
USE invoice_db;

-- -----------------------------------------------------------------------------
-- 1. Duplicate invoice detection (same invoice_number submitted more than once)
-- -----------------------------------------------------------------------------
SELECT i.invoice_number,
       COUNT(*)                       AS submissions,
       GROUP_CONCAT(i.invoice_id)     AS invoice_ids,
       GROUP_CONCAT(i.status)         AS statuses,
       SUM(i.total_amount)            AS exposure
FROM invoices i
GROUP BY i.invoice_number
HAVING COUNT(*) > 1
ORDER BY exposure DESC;

-- -----------------------------------------------------------------------------
-- 2. Vendor spending (total and share per vendor, paid + flagged included)
-- -----------------------------------------------------------------------------
SELECT v.vendor_name,
       COUNT(i.invoice_id)               AS invoice_count,
       ROUND(SUM(i.total_amount), 2)     AS total_spend,
       ROUND(SUM(i.total_amount) / (SELECT SUM(total_amount) FROM invoices) * 100, 2) AS spend_pct
FROM invoices i
JOIN vendors v ON v.vendor_id = i.vendor_id
GROUP BY v.vendor_id, v.vendor_name
ORDER BY total_spend DESC;

-- -----------------------------------------------------------------------------
-- 3. Monthly invoice trend (volume and value per month)
-- -----------------------------------------------------------------------------
SELECT DATE_FORMAT(i.invoice_date, '%Y-%m') AS month,
       COUNT(*)                               AS invoice_count,
       ROUND(SUM(i.total_amount), 2)          AS invoiced_amount,
       ROUND(AVG(i.total_amount), 2)          AS avg_amount
FROM invoices i
GROUP BY month
ORDER BY month;

-- -----------------------------------------------------------------------------
-- 4. High-risk invoices (top by risk, with vendor)
-- -----------------------------------------------------------------------------
SELECT i.invoice_id,
       i.invoice_number,
       v.vendor_name,
       i.invoice_date,
       i.total_amount,
       i.risk_score,
       i.status
FROM invoices i
JOIN vendors v ON v.vendor_id = i.vendor_id
WHERE i.status IN ('High Risk', 'Needs Review', 'Duplicate')
ORDER BY i.risk_score DESC
LIMIT 25;

-- -----------------------------------------------------------------------------
-- 5. Top 10 most expensive products (by line total)
-- -----------------------------------------------------------------------------
SELECT ii.product_name,
       COUNT(*)           AS line_count,
       ROUND(SUM(ii.quantity * ii.unit_price), 2) AS gross_value,
       ROUND(AVG(ii.unit_price), 2)                AS avg_unit_price,
       ROUND(MAX(ii.unit_price), 2)                AS max_unit_price
FROM invoice_items ii
GROUP BY ii.product_name
ORDER BY gross_value DESC
LIMIT 10;

-- -----------------------------------------------------------------------------
-- 6. GST / tax summary by rate (taxable base and tax collected per rate)
-- -----------------------------------------------------------------------------
SELECT ii.tax_percent                                  AS gst_rate,
       COUNT(ii.item_id)                               AS line_count,
       ROUND(SUM(ii.quantity * ii.unit_price), 2)      AS taxable_base,
       ROUND(SUM(ii.quantity * ii.unit_price * ii.tax_percent / 100), 2) AS tax_amount,
       ROUND(SUM(ii.line_total), 2)                    AS billed_amount
FROM invoice_items ii
GROUP BY ii.tax_percent
ORDER BY ii.tax_percent;

-- -----------------------------------------------------------------------------
-- 7. Pending invoices (not yet validated / paid)
-- -----------------------------------------------------------------------------
SELECT i.invoice_number, v.vendor_name, i.invoice_date,
       i.total_amount, i.status, DATEDIFF(CURDATE(), i.invoice_date) AS days_pending
FROM invoices i
JOIN vendors v ON v.vendor_id = i.vendor_id
WHERE i.status = 'Pending'
ORDER BY i.invoice_date;

-- -----------------------------------------------------------------------------
-- 8. Vendor-wise invoice count (incl. inactive/blacklisted visibility)
-- -----------------------------------------------------------------------------
SELECT v.vendor_name,
       v.status,
       COUNT(i.invoice_id) AS invoice_count
FROM vendors v
LEFT JOIN invoices i ON i.vendor_id = v.vendor_id
GROUP BY v.vendor_id, v.vendor_name, v.status
ORDER BY invoice_count DESC;

-- -----------------------------------------------------------------------------
-- 9. Average invoice value (overall and per vendor)
-- -----------------------------------------------------------------------------
SELECT ROUND(AVG(total_amount), 2) AS avg_invoice_value,
       ROUND(MIN(total_amount), 2) AS min_invoice_value,
       ROUND(MAX(total_amount), 2) AS max_invoice_value
FROM invoices;

-- per-vendor average, useful for the ML price-anomaly baseline
SELECT v.vendor_name,
       COUNT(i.invoice_id)           AS invoice_count,
       ROUND(AVG(i.total_amount), 2) AS avg_invoice_value
FROM invoices i
JOIN vendors v ON v.vendor_id = i.vendor_id
GROUP BY v.vendor_id, v.vendor_name
ORDER BY avg_invoice_value DESC;

-- -----------------------------------------------------------------------------
-- 10. Validation error summary (by type and severity) — decision-ready report
-- -----------------------------------------------------------------------------
SELECT vr.validation_type,
       vr.severity,
       COUNT(*) AS issue_count
FROM validation_results vr
GROUP BY vr.validation_type, vr.severity
ORDER BY FIELD(vr.severity, 'CRITICAL', 'ERROR', 'WARNING', 'INFO'), issue_count DESC;

-- -----------------------------------------------------------------------------
-- 11. Potential financial loss from flagged invoices
-- -----------------------------------------------------------------------------
SELECT ROUND(SUM(total_amount), 2) AS potential_loss
FROM invoices
WHERE status IN ('High Risk', 'Duplicate');

-- -----------------------------------------------------------------------------
-- 12. Payment reconciliation: paid invoices that earlier carried a mismatch flag
-- -----------------------------------------------------------------------------
SELECT i.invoice_number, v.vendor_name, i.total_amount, i.status,
       vr.validation_type, vr.severity, vr.message, vr.created_at
FROM validation_results vr
JOIN invoices i   ON i.invoice_id = vr.invoice_id
JOIN vendors v    ON v.vendor_id  = i.vendor_id
WHERE i.status = 'Paid'
  AND vr.validation_type IN ('TOTAL_MISMATCH', 'GST_MISMATCH')
ORDER BY vr.created_at;