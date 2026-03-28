import { pgTable, uuid, varchar, integer, date, decimal, timestamp, index } from 'drizzle-orm/pg-core'
import { generations } from './generations'
import { incomeBands } from './income-bands'
import { geography } from './geography'

// FR-6.9: Consumer panel structure (100,000-500,000 panelists)
export const panelists = pgTable('panelists', {
  id: uuid('id').primaryKey().defaultRandom(),
  incomeBandId: varchar('income_band_id', { length: 20 }).notNull().references(() => incomeBands.id),
  generationId: varchar('generation_id', { length: 20 }).notNull().references(() => generations.id),
  geographyId: integer('geography_id').notNull().references(() => geography.id),
  panelStartDate: date('panel_start_date').notNull(),
  panelWeight: decimal('panel_weight', { precision: 10, scale: 4 }).notNull(),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
}, (table) => [
  index('idx_panelists_weight').on(table.panelWeight),
  index('idx_panelists_income_band').on(table.incomeBandId),
  index('idx_panelists_generation').on(table.generationId),
  index('idx_panelists_geography').on(table.geographyId),
  index('idx_panelists_start_date').on(table.panelStartDate),
])

export type Panelist = typeof panelists.$inferSelect
export type NewPanelist = typeof panelists.$inferInsert
