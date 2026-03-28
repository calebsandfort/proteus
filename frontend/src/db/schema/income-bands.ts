import { pgTable, varchar, integer, decimal, timestamp } from 'drizzle-orm/pg-core'

// FR-6.6: Income multipliers affecting transaction amounts
export const incomeBands = pgTable('income_bands', {
  id: varchar('id', { length: 20 }).primaryKey(),
  name: varchar('name', { length: 50 }).notNull(),
  minIncome: integer('min_income').notNull(),
  maxIncome: integer('max_income'),
  incomeMultiplier: decimal('income_multiplier', { precision: 4, scale: 2 }).notNull().default('1.0'),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
})

export type IncomeBand = typeof incomeBands.$inferSelect
export type NewIncomeBand = typeof incomeBands.$inferInsert
