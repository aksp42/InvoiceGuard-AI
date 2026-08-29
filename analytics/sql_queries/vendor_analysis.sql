-- Vendor-wise average invoice amount and volume
SELECT v.vendor_name,
       ROUND(AVG(i.total_amount), 2) AS avg_invoice_amount,
       COUNT(*)                       AS invoice_count
FROM invoices i
JOIN vendors v ON v.vendor_id = i.vendor_id
GROUP BY v.vendor_name
ORDER BY avg_invoice_amount DESC;