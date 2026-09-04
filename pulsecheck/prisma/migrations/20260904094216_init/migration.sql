-- CreateEnum
CREATE TYPE "OrgTier" AS ENUM ('agency', 'enterprise');

-- CreateEnum
CREATE TYPE "ModeratorRole" AS ENUM ('owner', 'admin', 'member');

-- CreateEnum
CREATE TYPE "SessionType" AS ENUM ('concept_test', 'ad_recall', 'brand_pulse', 'focus_group', 'custom');

-- CreateEnum
CREATE TYPE "SessionStatus" AS ENUM ('draft', 'live', 'ended');

-- CreateEnum
CREATE TYPE "SlideType" AS ENUM ('poll', 'word_cloud', 'rating_scale', 'open_text');

-- CreateEnum
CREATE TYPE "InsightSource" AS ENUM ('pulsecheck', 'mediapulse');

-- CreateTable
CREATE TABLE "organizations" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "tier" "OrgTier" NOT NULL DEFAULT 'agency',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "organizations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "org_id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "password_hash" TEXT NOT NULL,
    "role" "ModeratorRole" NOT NULL DEFAULT 'owner',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "sessions" (
    "id" TEXT NOT NULL,
    "org_id" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "type" "SessionType" NOT NULL DEFAULT 'custom',
    "status" "SessionStatus" NOT NULL DEFAULT 'draft',
    "join_code" TEXT NOT NULL,
    "created_by_id" TEXT,
    "active_slide_order" INTEGER,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "started_at" TIMESTAMP(3),
    "ended_at" TIMESTAMP(3),

    CONSTRAINT "sessions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "session_slides" (
    "id" TEXT NOT NULL,
    "session_id" TEXT NOT NULL,
    "order" INTEGER NOT NULL,
    "type" "SlideType" NOT NULL,
    "config" JSONB NOT NULL DEFAULT '{}',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "session_slides_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "participants" (
    "id" TEXT NOT NULL,
    "session_id" TEXT NOT NULL,
    "join_code" TEXT NOT NULL,
    "device_fingerprint" TEXT,
    "demographic_tags" JSONB NOT NULL DEFAULT '{}',
    "joined_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "participants_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "responses" (
    "id" TEXT NOT NULL,
    "session_id" TEXT NOT NULL,
    "slide_id" TEXT NOT NULL,
    "participant_id" TEXT NOT NULL,
    "value" JSONB NOT NULL,
    "submitted_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "responses_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "insight_records" (
    "id" TEXT NOT NULL,
    "org_id" TEXT NOT NULL,
    "source" "InsightSource" NOT NULL DEFAULT 'pulsecheck',
    "record_type" TEXT NOT NULL,
    "summary" TEXT NOT NULL,
    "tags" JSONB NOT NULL DEFAULT '{}',
    "linked_session_id" TEXT,
    "linked_article_id" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "insight_records_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE INDEX "users_org_id_idx" ON "users"("org_id");

-- CreateIndex
CREATE UNIQUE INDEX "sessions_join_code_key" ON "sessions"("join_code");

-- CreateIndex
CREATE INDEX "sessions_org_id_idx" ON "sessions"("org_id");

-- CreateIndex
CREATE INDEX "session_slides_session_id_idx" ON "session_slides"("session_id");

-- CreateIndex
CREATE UNIQUE INDEX "session_slides_session_id_order_key" ON "session_slides"("session_id", "order");

-- CreateIndex
CREATE INDEX "participants_session_id_idx" ON "participants"("session_id");

-- CreateIndex
CREATE INDEX "responses_session_id_idx" ON "responses"("session_id");

-- CreateIndex
CREATE INDEX "responses_slide_id_idx" ON "responses"("slide_id");

-- CreateIndex
CREATE UNIQUE INDEX "responses_slide_id_participant_id_key" ON "responses"("slide_id", "participant_id");

-- CreateIndex
CREATE INDEX "insight_records_org_id_idx" ON "insight_records"("org_id");

-- CreateIndex
CREATE INDEX "insight_records_source_idx" ON "insight_records"("source");

-- AddForeignKey
ALTER TABLE "users" ADD CONSTRAINT "users_org_id_fkey" FOREIGN KEY ("org_id") REFERENCES "organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "sessions" ADD CONSTRAINT "sessions_org_id_fkey" FOREIGN KEY ("org_id") REFERENCES "organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "sessions" ADD CONSTRAINT "sessions_created_by_id_fkey" FOREIGN KEY ("created_by_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "session_slides" ADD CONSTRAINT "session_slides_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "sessions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "participants" ADD CONSTRAINT "participants_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "sessions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "responses" ADD CONSTRAINT "responses_session_id_fkey" FOREIGN KEY ("session_id") REFERENCES "sessions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "responses" ADD CONSTRAINT "responses_slide_id_fkey" FOREIGN KEY ("slide_id") REFERENCES "session_slides"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "responses" ADD CONSTRAINT "responses_participant_id_fkey" FOREIGN KEY ("participant_id") REFERENCES "participants"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "insight_records" ADD CONSTRAINT "insight_records_org_id_fkey" FOREIGN KEY ("org_id") REFERENCES "organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "insight_records" ADD CONSTRAINT "insight_records_linked_session_id_fkey" FOREIGN KEY ("linked_session_id") REFERENCES "sessions"("id") ON DELETE SET NULL ON UPDATE CASCADE;
