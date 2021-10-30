-- upgrade --
ALTER TABLE "post" ADD "description" TEXT;
-- downgrade --
ALTER TABLE "post" DROP COLUMN "description";
