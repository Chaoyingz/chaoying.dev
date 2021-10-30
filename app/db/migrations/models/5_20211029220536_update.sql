-- upgrade --
ALTER TABLE "post" ADD "toc" TEXT;
-- downgrade --
ALTER TABLE "post" DROP COLUMN "toc";
