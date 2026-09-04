import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";

const prisma = new PrismaClient();

async function main() {
  const org = await prisma.organization.upsert({
    where: { id: "seed-org" },
    update: {},
    create: { id: "seed-org", name: "Kalahari Insights (demo)", tier: "agency" },
  });

  const passwordHash = await bcrypt.hash("password123", 10);
  await prisma.user.upsert({
    where: { email: "demo@pulsecheck.bw" },
    update: {},
    create: {
      orgId: org.id,
      name: "Demo Moderator",
      email: "demo@pulsecheck.bw",
      passwordHash,
      role: "owner",
    },
  });

  const session = await prisma.session.upsert({
    where: { id: "seed-session" },
    update: {},
    create: {
      id: "seed-session",
      orgId: org.id,
      title: "Beverage Brand X — Concept Test",
      type: "concept_test",
      joinCode: "123456",
      status: "draft",
    },
  });

  await prisma.sessionSlide.deleteMany({ where: { sessionId: session.id } });
  await prisma.sessionSlide.createMany({
    data: [
      {
        sessionId: session.id,
        order: 0,
        type: "poll",
        config: {
          question: "Which concept do you prefer?",
          options: ["Concept A", "Concept B", "Concept C"],
          multi: false,
        },
      },
      {
        sessionId: session.id,
        order: 1,
        type: "rating_scale",
        config: {
          question: "How likely are you to purchase this product?",
          min: 1,
          max: 5,
          minLabel: "Not likely",
          maxLabel: "Very likely",
        },
      },
      {
        sessionId: session.id,
        order: 2,
        type: "word_cloud",
        config: { prompt: "Describe this brand in one word", maxWords: 1 },
      },
      {
        sessionId: session.id,
        order: 3,
        type: "open_text",
        config: { prompt: "What would make you more likely to buy this?" },
      },
    ],
  });

  console.log(`Seeded org "${org.name}" — login demo@pulsecheck.bw / password123`);
  console.log(`Demo session join code: ${session.joinCode}`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
