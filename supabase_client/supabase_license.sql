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
