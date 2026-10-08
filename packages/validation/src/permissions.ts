import { z } from 'zod';

export const rolePermissionInputSchema = z.object({
  permission_code: z.string().min(1, 'Permission code is required'),
  scope_code: z.string().optional().default('GLOBAL'),
  scope_parameters: z.record(z.any()).optional().default({}),
});

export const roleCreateSchema = z.object({
  code: z
    .string()
    .optional()
    .transform((val) => (val ? val.trim().toUpperCase().replace(/\s+/g, '_') : undefined)),
  name: z.string().min(2, 'Role name must be at least 2 characters long').trim(),
  description: z.string().optional().default(''),
  is_active: z.boolean().optional().default(true),
  permissions: z.array(rolePermissionInputSchema).optional().default([]),
});

export type RoleCreateInput = z.infer<typeof roleCreateSchema>;

export const roleUpdateSchema = z.object({
  name: z.string().min(2).optional(),
  description: z.string().optional(),
  is_active: z.boolean().optional(),
  permissions: z.array(rolePermissionInputSchema).optional(),
});

export type RoleUpdateInput = z.infer<typeof roleUpdateSchema>;

export const roleAssignmentSchema = z
  .object({
    role_code: z.string().optional(),
    role_uuid: z.string().uuid().optional(),
    expires_at: z.string().datetime().nullable().optional(),
    scope_override_code: z.string().nullable().optional(),
    scope_context: z.record(z.any()).optional().default({}),
  })
  .refine((data) => Boolean(data.role_code || data.role_uuid), {
    message: 'Either role_code or role_uuid must be provided',
    path: ['role_code'],
  });

export type RoleAssignmentInput = z.infer<typeof roleAssignmentSchema>;
