import { z } from 'zod';

export const academicsSchema = z.object({});

export type AcademicsSchema = z.infer<typeof academicsSchema>;
