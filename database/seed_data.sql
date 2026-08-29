-- =============================================================================
-- Invoice Error Detector — seed data  (Phase 2: database, Phase 2.1: hardening)
-- 1 company, 5 vendors, 20 invoices, 61 line items, 16 validation records,
-- 3 upload batches. Invoices link to their originating batch where known.
-- Totals are generated so that subtotal + tax = total for every invoice.
-- =============================================================================

USE invoice_db;

-- ----------------------------------------------------------------------
-- 1. Companies
-- ----------------------------------------------------------------------
INSERT INTO companies (company_id, company_name, gst_number, email) VALUES
  (1, 'Akshu Enterprises Pvt Ltd', '27AACCA9603R1ZM', 'accounts@akshuenterprises.com');

-- ----------------------------------------------------------------------
-- 2. Vendors
-- ----------------------------------------------------------------------
INSERT INTO vendors (vendor_id, company_id, vendor_name, gst_number, email, phone, status) VALUES
  (1, 1, 'ABC Traders', '27ABCDE1234F1Z5', 'abc.traders@gmail.com', '+91-98200-11111', 'Active'),
  (2, 1, 'XYZ Supplies', '29XYZAB5678G1Z2', 'xyz.supplies@gmail.com', '+91-98200-22222', 'Active'),
  (3, 1, 'Metro Electronics', '07METRO9988R1Z3', 'metro.electronics@gmail.com', '+91-98200-33333', 'Blacklisted'),
  (4, 1, 'Global Hardware', '36GLOBL1224K1Z7', 'global.hardware@outlook.com', '+91-98200-44444', 'Active'),
  (5, 1, 'Prime Stationery', '19PRIME3344L1Z1', 'prime.stationery@gmail.com', '+91-98200-55555', 'Active'));

-- ----------------------------------------------------------------------
-- 3. Invoices (header) — amounts computed from line items
--    batch_id links each invoice to the upload batch that created it
-- ----------------------------------------------------------------------
INSERT INTO invoices (invoice_id, company_id, vendor_id, invoice_number, invoice_date, subtotal, tax_amount, total_amount, status, risk_score, batch_id) VALUES
  (1, 1, 1, 'ABC-2024-0118', '2024-01-05', 15020.00, 2354.40, 17374.40, 'Paid', 4.20, 1),
  (2, 1, 1, 'ABC-2024-0133', '2024-02-12', 7950.00, 954.00, 8904.00, 'Paid', 2.10, 1),
  (3, 1, 1, 'ABC-2024-0201', '2024-03-02', 8400.00, 1362.00, 9762.00, 'Valid', 6.50, 1),
  (4, 1, 1, 'ABC-2024-0247', '2024-04-18', 25200.00, 4422.00, 29622.00, 'Needs Review', 42.00, 1),
  (5, 1, 2, 'XYZ-2024-0099', '2024-01-20', 38900.00, 7002.00, 45902.00, 'Paid', 5.00, 1),
  (6, 1, 2, 'XYZ-2024-0099', '2024-01-20', 38900.00, 7002.00, 45902.00, 'Duplicate', 100.00, 1),
  (7, 1, 2, 'XYZ-2024-0144', '2024-03-15', 24450.00, 4401.00, 28851.00, 'Valid', 8.30, 1),
  (8, 1, 2, 'XYZ-2024-0178', '2024-04-30', 35550.00, 6399.00, 41949.00, 'Pending', 0.00, 1),
  (9, 1, 1, 'ABC-2024-0118', '2024-01-05', 15020.00, 2354.40, 17374.40, 'Duplicate', 100.00, 1),
  (10, 1, 3, 'MET-2024-0005', '2024-02-14', 62300.00, 11214.00, 73514.00, 'Paid', 3.40, 1),
  (11, 1, 3, 'MET-2024-0022', '2024-03-28', 48500.00, 8730.00, 57230.00, 'Valid', 7.10, 1),
  (12, 1, 3, 'MET-2024-0036', '2024-05-08', 26400.00, 4428.00, 30828.00, 'Needs Review', 45.00, 1),
  (13, 1, 3, 'MET-2024-0051', '2024-06-03', 42620.00, 7671.60, 50291.60, 'High Risk', 68.00, 2),
  (14, 1, 4, 'GLO-2024-0101', '2024-02-25', 25700.00, 4626.00, 30326.00, 'Pending', 0.00, 2),
  (15, 1, 4, 'GLO-2024-0117', '2024-04-05', 36700.00, 6606.00, 43306.00, 'Needs Review', 39.00, 3),
  (16, 1, 4, 'GLO-2024-0140', '2024-05-12', 46400.00, 8352.00, 54752.00, 'Pending', 0.00, 3),
  (17, 1, 4, 'GLO-2024-0158', '2027-03-01', 16900.00, 3042.00, 19942.00, 'High Risk', 62.00, 3),
  (18, 1, 5, 'PRI-2024-0020', '2024-03-10', 78500.00, 9420.00, 87920.00, 'High Risk', 71.00, NULL),
  (19, 1, 5, 'PRI-2024-0033', '2024-04-22', 31000.00, 3720.00, 34720.00, 'High Risk', 88.00, NULL),
  (20, 1, 5, 'PRI-2024-0047', '2024-06-15', 204600.00, 24552.00, 229152.00, 'High Risk', 74.00, NULL));

-- ----------------------------------------------------------------------
-- 4. Invoice items (61 rows)
-- ----------------------------------------------------------------------
INSERT INTO invoice_items (invoice_id, product_name, quantity, unit_price, tax_percent, line_total) VALUES
  (1, 'A4 Paper Ream', 25, 180.00, 12, 5040.00),
  (1, 'Printer Ink Cartridge', 8, 1150.00, 18, 10856.00),
  (1, 'File Folders', 60, 22.00, 12, 1478.40),
  (2, 'A4 Paper Ream', 20, 185.00, 12, 4144.00),
  (2, 'Stapler HD-12', 10, 245.00, 12, 2744.00),
  (2, 'Staples Box', 30, 60.00, 12, 2016.00),
  (3, 'Printer Ink Cartridge', 5, 1180.00, 18, 6962.00),
  (3, 'Whiteboard Markers', 20, 95.00, 12, 2128.00),
  (3, 'Paper Clips', 40, 15.00, 12, 672.00),
  (4, 'Laser Printer Toner', 4, 4200.00, 18, 19824.00),
  (4, 'A4 Paper Ream', 10, 190.00, 12, 2128.00),
  (4, 'Binding Machine', 1, 6500.00, 18, 7670.00),
  (5, 'Steel Rod 10mm', 120, 180.00, 18, 25488.00),
  (5, 'Copper Wire 1.5mm', 40, 320.00, 18, 15104.00),
  (5, 'Nuts & Bolts Pack', 30, 150.00, 18, 5310.00),
  (6, 'Steel Rod 10mm', 120, 180.00, 18, 25488.00),
  (6, 'Copper Wire 1.5mm', 40, 320.00, 18, 15104.00),
  (6, 'Nuts & Bolts Pack', 30, 150.00, 18, 5310.00),
  (7, 'Aluminium Sheet', 45, 260.00, 18, 13806.00),
  (7, 'PVC Pipe 4"', 25, 340.00, 18, 10030.00),
  (7, 'Industrial Gloves', 50, 85.00, 18, 5015.00),
  (8, 'Steel Rod 12mm', 90, 210.00, 18, 22302.00),
  (8, 'Welding Wire', 15, 550.00, 18, 9735.00),
  (8, 'Angle Iron', 60, 140.00, 18, 9912.00),
  (9, 'A4 Paper Ream', 25, 180.00, 12, 5040.00),
  (9, 'Printer Ink Cartridge', 8, 1150.00, 18, 10856.00),
  (9, 'File Folders', 60, 22.00, 12, 1478.40),
  (10, 'LED Monitor 24"', 5, 8200.00, 18, 48380.00),
  (10, 'Wireless Keyboard', 10, 1450.00, 18, 17110.00),
  (10, 'Wireless Mouse', 10, 680.00, 18, 8024.00),
  (11, 'UPS 1kVA', 6, 5600.00, 18, 39648.00),
  (11, 'HDMI Cable', 25, 240.00, 18, 7080.00),
  (11, 'USB-C Hub', 10, 890.00, 18, 10502.00),
  (12, 'Thermal Printer', 3, 3800.00, 18, 13452.00),
  (12, 'Router Dual Band', 4, 2400.00, 18, 11328.00),
  (12, 'Surge Protector', 12, 450.00, 12, 6048.00),
  (13, 'LED Monitor 24"', 4, 8150.00, 18, 38468.00),
  (13, 'Wireless Mouse', 8, 690.00, 18, 6513.60),
  (13, 'USB-C Cable', 30, 150.00, 18, 5310.00),
  (14, 'Power Drill 700W', 3, 3200.00, 18, 11328.00),
  (14, 'Drill Bit Set', 6, 850.00, 18, 6018.00),
  (14, 'Toolbox', 10, 1100.00, 18, 12980.00),
  (15, 'Circular Saw 1800W', 2, 6800.00, 18, 16048.00),
  (15, 'Angle Grinder', 5, 3900.00, 18, 23010.00),
  (15, 'Safety Goggles', 20, 180.00, 18, 4248.00),
  (16, 'Power Drill 1000W', 4, 4500.00, 18, 21240.00),
  (16, 'Impact Wrench', 2, 7200.00, 18, 16992.00),
  (16, 'Tool Cabinet', 1, 14000.00, 18, 16520.00),
  (17, 'Angle Grinder 900W', 3, 3500.00, 18, 12390.00),
  (17, 'Cutting Disc Pack', 15, 120.00, 18, 2124.00),
  (17, 'Grinder Stand', 2, 2300.00, 18, 5428.00),
  (18, 'Ball Pens (Pack 10)', 500, 45.00, 12, 25200.00),
  (18, 'Notebooks A5', 300, 60.00, 12, 20160.00),
  (18, 'Gel Pens (Pack 5)', 400, 95.00, 12, 42560.00),
  (19, 'Sticky Notes Pack', 250, 30.00, 12, 8400.00),
  (19, 'Desk Organizer', 30, 350.00, 12, 11760.00),
  (19, 'Highlighter Set', 200, 65.00, 12, 14560.00),
  (20, 'Executive Chair', 15, 8500.00, 12, 142800.00),
  (20, 'Whiteboard 6x4', 8, 3200.00, 12, 28672.00),
  (20, 'Presentation Clicker', 25, 1100.00, 12, 30800.00),
  (20, 'Laminator A4', 5, 4800.00, 12, 26880.00));

-- ----------------------------------------------------------------------
-- 5. Upload batches (3 records) — linked from invoices.batch_id
--    1 = Completed (invoices 1-12), 2 = Failed (invoices 13-14 stored),
--    3 = Processing (invoices 15-17 stored so far)
-- ----------------------------------------------------------------------
INSERT INTO upload_batches (batch_id, file_name, uploaded_by, uploaded_at, total_invoices, processed_invoices, failed_invoices, status) VALUES
  (1, 'jan_2024_invoices.csv', 'admin',   '2024-01-10 09:15:00', 12, 12, 0, 'Completed'),
  (2, 'apr_import_mixed.xlsx', 'admin',   '2024-04-02 14:30:00',  3,  2, 1, 'Failed'),
  (3, 'june_2024_bulk.xlsx',   'ap_team', '2024-05-20 11:05:00',  5,  3, 0, 'Processing');

-- ----------------------------------------------------------------------
-- 6. Validation results (16 records)
-- ----------------------------------------------------------------------
INSERT INTO validation_results (invoice_id, validation_type, severity, message, confidence_score) VALUES
  (1, 'RISK_ANOMALY', 'INFO', 'All automated checks passed.', 95.50),
  (4, 'PRICE_OUTLIER', 'WARNING', 'Unit price Rs 4,200.00 (Laser Printer Toner) unusually high - review recommended.', 88.50),
  (6, 'DUPLICATE', 'ERROR', 'Invoice number XYZ-2024-0099 has already been submitted.', 99.20),
  (9, 'DUPLICATE', 'ERROR', 'Invoice number ABC-2024-0118 has already been submitted.', 99.20),
  (10, 'RISK_ANOMALY', 'INFO', 'All automated checks passed.', 95.50),
  (12, 'GST_MISMATCH', 'WARNING', 'GST calculation mismatch: expected rate on Surge Protector is 12%, invoice applies 18%.', 94.80),
  (13, 'TOTAL_MISMATCH', 'ERROR', 'Total mismatch: expected Rs 44,902.80, got Rs 44,452.80.', 97.40),
  (15, 'PRICE_OUTLIER', 'WARNING', 'Unit price Rs 6,800.00 (Circular Saw) unusually high - review recommended.', 88.50),
  (17, 'FUTURE_DATE', 'ERROR', 'Invoice dated in the future: 2027-03-01.', 95.10),
  (18, 'RISK_ANOMALY', 'WARNING', 'Invoice deviates strongly from vendor pricing history (Isolation Forest anomaly).', 86.70),
  (19, 'MISSING_FIELD', 'ERROR', 'Missing required field: vendor_name on submitted record.', 99.90),
  (20, 'RISK_ANOMALY', 'WARNING', 'Invoice deviates strongly from vendor pricing history (Isolation Forest anomaly).', 86.70),
  (20, 'PRICE_OUTLIER', 'WARNING', 'Unit price Rs 8,500.00 (Executive Chair) unusually high - review recommended.', 88.50),
  (1, 'RECONCILIATION', 'INFO', 'Payment reconciled against bank statement.', 99.00),
  (5, 'RECONCILIATION', 'INFO', 'Payment reconciled against bank statement.', 99.00),
  (10, 'RECONCILIATION', 'INFO', 'Payment reconciled against bank statement.', 99.00);
