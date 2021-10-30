-- upgrade --
ALTER TABLE "post" ADD "source" TEXT;
-- downgrade --
ALTER TABLE "post" DROP COLUMN "source";
