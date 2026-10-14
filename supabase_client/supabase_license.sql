-- Cereate pg_cron to run the  below function daily
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Daily batch run to update lience key status
-- Create a function that performs the expiration check and update
CREATE OR REPLACE FUNCTION public.check_and_disable_expired_licenses()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE public.licenses -- Replace 'licenses' with your actual table name if different
  SET status = LOWER('Disabled')
  WHERE status = LOWER('Active')
    AND expiry_date_time IS NOT NULL
    AND expiry_date_time <= NOW();
END;
$$;

-- Schedule the function to run daily
SELECT cron.schedule(
  'disable-expired-licenses-daily', -- Job name
  '0 3 * * *',                      -- Cron schedule (Every day at 03:00 / 3:00 AM UTC)
  $$SELECT public.check_and_disable_expired_licenses();$$
);

-- Check if the scheduled job is existing
SELECT * FROM cron.job;

-- Scheduled Jobs Logs
-- Check Job Execution History & Logs
SELECT j.jobname, d.status, d.return_message, d.start_time, d.end_time 
FROM cron.job_run_details d
JOIN cron.job j ON d.jobid = j.jobid
ORDER BY d.start_time DESC 
LIMIT 10;

-- Modify or Re-create the Job via SQL
-- 1. Remove the old job if it exists
SELECT cron.unschedule('disable-expired-licenses-daily');

-- 2. Re-create it fresh
SELECT cron.schedule(
  'disable-expired-licenses-daily',
  '0 0 * * *',
  $$SELECT public.check_and_disable_expired_licenses();$$
);

-- 1. Remove the existing job
SELECT cron.unschedule('disable-expired-licenses-daily');

-- 2. Create it with the new 3:00 AM schedule
SELECT cron.schedule(
  'disable-expired-licenses-daily',
  '0 3 * * *',
  $$SELECT public.check_and_disable_expired_licenses();$$
);

-- 1. Remove the existing job
SELECT cron.unschedule('disable-expired-licenses-daily');

-- 2. Re-create it to run every day at 23:55
SELECT cron.schedule(
  'disable-expired-licenses-daily',
  '55 23 * * *',
  $$SELECT public.check_and_disable_expired_licenses();$$
);

-- For NZ time zone at 23:55
-- 1. Remove the old schedule
SELECT cron.unschedule('disable-expired-licenses-daily');

-- 2. Schedule it for 10:55 UTC (which equals 23:55 / 11:55 PM NZDT)
SELECT cron.schedule(
  'disable-expired-licenses-daily',
  '55 10 * * *', 
  $$SELECT public.check_and_disable_expired_licenses();$$
);

-- Check the Execution Logs
SELECT j.jobname, d.* 
FROM cron.job_run_details d
JOIN cron.job j ON d.jobid = j.jobid
WHERE j.jobname = 'disable-expired-licenses-daily' 
ORDER BY d.start_time DESC 
LIMIT 5;

-- Check if the scheduled job is existing
-- Get the latest jobid = 5
SELECT * FROM cron.job;

-- Check all job run logs
select * from cron.job_run_details
order by runid desc;
