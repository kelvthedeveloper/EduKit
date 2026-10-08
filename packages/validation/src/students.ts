import { z } from 'zod';

export const studentsSchema = z.object({});

export type StudentsSchema = z.infer<typeof studentsSchema>;
