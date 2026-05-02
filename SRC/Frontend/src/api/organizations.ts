import {
  MOCK_ENABLED,
  mockAbortOrganization,
  mockActivateOrganization,
  mockCreateOrganization,
  mockDeactivateOrganization,
  mockGetOrganization,
  mockListOrganizations,
  mockPatchOrganization,
  mockReportOrganization,
  mockSuspendOrganization,
} from "../lib/adminMockData"
import { api } from "./client"
import type { OrganizationDetail, OrganizationListItem, Paginated } from "./types"

export type ListOrganizationsParams = {
  page?: number
  page_size?: number
  status?: string
  search?: string
}

export async function listOrganizations(params?: ListOrganizationsParams): Promise<Paginated<OrganizationListItem>> {
  if (MOCK_ENABLED) return mockListOrganizations(params)
  const res = await api.get<Paginated<OrganizationListItem>>("/organizations", { params })
  return res.data
}

export async function getOrganization(id: string): Promise<OrganizationDetail> {
  if (MOCK_ENABLED) return mockGetOrganization(id)
  const res = await api.get<OrganizationDetail>(`/organizations/${id}`)
  return res.data
}

export async function createOrganization(body: { name: string; domain: string }): Promise<OrganizationDetail> {
  if (MOCK_ENABLED) return mockCreateOrganization(body)
  const res = await api.post<OrganizationDetail>("/organizations", body)
  return res.data
}

export async function patchOrganization(
  id: string,
  body: { name?: string; domain?: string },
): Promise<OrganizationDetail> {
  if (MOCK_ENABLED) return mockPatchOrganization(id, body)
  const res = await api.patch<OrganizationDetail>(`/organizations/${id}`, body)
  return res.data
}

export async function activateOrganization(id: string): Promise<OrganizationDetail> {
  if (MOCK_ENABLED) return mockActivateOrganization(id)
  const res = await api.post<OrganizationDetail>(`/organizations/${id}/activate`)
  return res.data
}

export async function deactivateOrganization(id: string): Promise<OrganizationDetail> {
  if (MOCK_ENABLED) return mockDeactivateOrganization(id)
  const res = await api.post<OrganizationDetail>(`/organizations/${id}/deactivate`)
  return res.data
}

export async function suspendOrganization(id: string): Promise<OrganizationDetail> {
  if (MOCK_ENABLED) return mockSuspendOrganization(id)
  const res = await api.post<OrganizationDetail>(`/organizations/${id}/suspend`)
  return res.data
}

export async function abortOrganization(id: string): Promise<OrganizationDetail> {
  if (MOCK_ENABLED) return mockAbortOrganization(id)
  const res = await api.post<OrganizationDetail>(`/organizations/${id}/abort`)
  return res.data
}

export async function reportOrganization(id: string, notes: string): Promise<OrganizationDetail> {
  if (MOCK_ENABLED) return mockReportOrganization(id, notes)
  const res = await api.post<OrganizationDetail>(`/organizations/${id}/report`, { notes })
  return res.data
}
