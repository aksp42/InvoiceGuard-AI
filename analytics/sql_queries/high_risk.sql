-- High-risk invoices requiring manual attention
SELECT invoice_id, vendor_id, total_amount, risk_score, status
FROM invoices
WHERE status = 'High Risk'
ORDER BY risk_score DESC;