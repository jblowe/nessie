BEGIN TRANSACTION;

DELETE FROM apscheduler_jobs WHERE id = 'JOB_GENERATE_ALL_TABLES';

COMMIT TRANSACTION;
