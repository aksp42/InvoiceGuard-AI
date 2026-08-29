-- Duplicate invoice submissions (risk of double payment)
SELECT invoice_id, COUNT(*) AS submissions
FROM invoices
GROUP BY invoice_id
HAVING COUNT(*) > 1;