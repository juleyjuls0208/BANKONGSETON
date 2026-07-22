BEGIN;

-- Card UIDs are 4-byte or 7-byte RFID values. Never truncate or strip zeroes.
ALTER TABLE users ALTER COLUMN id_card_number TYPE varchar(14);
ALTER TABLE users ALTER COLUMN money_card_number TYPE varchar(14);
ALTER TABLE money_accounts ALTER COLUMN money_card_number TYPE varchar(14);
ALTER TABLE money_accounts ALTER COLUMN student_id_card TYPE varchar(14);
ALTER TABLE money_accounts ALTER COLUMN balance TYPE numeric(14,2);
ALTER TABLE money_accounts ALTER COLUMN total_loaded TYPE numeric(14,2);
ALTER TABLE transactions_log ALTER COLUMN money_card_number TYPE varchar(14);
ALTER TABLE lost_card_reports ALTER COLUMN old_card_number TYPE varchar(14);
ALTER TABLE lost_card_reports ALTER COLUMN new_card_number TYPE varchar(14);
ALTER TABLE virtual_cards ALTER COLUMN money_card_number TYPE varchar(14);

CREATE UNIQUE INDEX IF NOT EXISTS uq_money_accounts_card_nonblank
  ON money_accounts (money_card_number)
  WHERE NULLIF(trim(money_card_number), '') IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_transactions_log_transaction_id
  ON transactions_log (transaction_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_id_card_nonblank
  ON users (id_card_number)
  WHERE NULLIF(trim(id_card_number), '') IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_money_card_nonblank
  ON users (money_card_number)
  WHERE NULLIF(trim(money_card_number), '') IS NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'users_id_card_uid_format') THEN
    ALTER TABLE users ADD CONSTRAINT users_id_card_uid_format
      CHECK (id_card_number IS NULL OR trim(id_card_number) = '' OR id_card_number ~ '^[0-9A-Fa-f]{8}([0-9A-Fa-f]{6})?$');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'users_money_card_uid_format') THEN
    ALTER TABLE users ADD CONSTRAINT users_money_card_uid_format
      CHECK (money_card_number IS NULL OR trim(money_card_number) = '' OR money_card_number ~ '^[0-9A-Fa-f]{8}([0-9A-Fa-f]{6})?$');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'money_accounts_uid_format') THEN
    ALTER TABLE money_accounts ADD CONSTRAINT money_accounts_uid_format
      CHECK (money_card_number ~ '^[0-9A-Fa-f]{8}([0-9A-Fa-f]{6})?$');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'money_accounts_balance_nonnegative') THEN
    ALTER TABLE money_accounts ADD CONSTRAINT money_accounts_balance_nonnegative
      CHECK (balance >= 0 AND balance <> 'NaN'::numeric AND balance <> 'Infinity'::numeric AND balance <> '-Infinity'::numeric);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'money_accounts_total_loaded_nonnegative') THEN
    ALTER TABLE money_accounts ADD CONSTRAINT money_accounts_total_loaded_nonnegative
      CHECK (total_loaded >= 0 AND total_loaded <> 'NaN'::numeric AND total_loaded <> 'Infinity'::numeric AND total_loaded <> '-Infinity'::numeric);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'transactions_amount_finite') THEN
    ALTER TABLE transactions_log ADD CONSTRAINT transactions_amount_finite
      CHECK (amount <> 'NaN'::numeric AND amount <> 'Infinity'::numeric AND amount <> '-Infinity'::numeric);
  END IF;
END $$;

COMMIT;
