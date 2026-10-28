
-- QUERY 1: Patient demographics
SELECT
    gender,
    COUNT(*) AS total_patients
FROM patients
GROUP BY gender
ORDER BY total_patients DESC;


-- QUERY 2: Monthly healthcare utilization
SELECT
    substr(start, 1, 7) AS month,
    COUNT(*) AS total_encounters,
    COUNT(DISTINCT patient) AS unique_patients
FROM encounters
WHERE start IS NOT NULL
GROUP BY substr(start, 1, 7)
ORDER BY month;


-- QUERY 3: Encounter costs by type
SELECT
    encounterclass,
    COUNT(*) AS total_encounters,
    ROUND(SUM(CAST(total_claim_cost AS REAL)), 2)
        AS total_claim_cost,
    ROUND(AVG(CAST(total_claim_cost AS REAL)), 2)
        AS average_claim_cost
FROM encounters
GROUP BY encounterclass
ORDER BY total_claim_cost DESC;


-- QUERY 4: Most frequently recorded conditions
SELECT
    description AS condition_name,
    COUNT(*) AS condition_records,
    COUNT(DISTINCT patient) AS unique_patients
FROM conditions
WHERE description IS NOT NULL
GROUP BY description
ORDER BY unique_patients DESC
LIMIT 10;


-- QUERY 5: Encounter data quality
SELECT
    COUNT(*) AS total_encounters,
    SUM(CASE WHEN patient IS NULL
             THEN 1 ELSE 0 END) AS missing_patient_ids,
    SUM(CASE WHEN start IS NULL
             THEN 1 ELSE 0 END) AS missing_start_dates,
    SUM(CASE WHEN stop IS NOT NULL
              AND start IS NOT NULL
              AND stop < start
             THEN 1 ELSE 0 END) AS invalid_date_ranges
FROM encounters;
