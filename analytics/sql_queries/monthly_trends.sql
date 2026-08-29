-- Monthly anomaly trend (high-risk & duplicate counts per month)
SELECT DATE_FORMAT(invoice_date, '%Y-%m') AS month,
       SUM(CASE WHEN status = 'High Risk' THEN 1 ELSE 0 END) AS high_risk_count,
       SUM(CASE WHEN status = 'Duplicate' THEN 1 ELSE 0 END) AS duplicate_count,
       COUNT(*) AS total_invoices
FROM invoices
GROUP BY month
ORDER BY month;