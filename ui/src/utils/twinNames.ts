// Map twin IDs to Indian names
export const twinNames: Record<string, string> = {
  twin_001: 'Arjun',
  twin_002: 'Priya',
  twin_003: 'Vikram',
  twin_004: 'Anjali',
  twin_005: 'Rajesh',
  twin_006: 'Kavya',
  twin_007: 'Aditya',
  twin_008: 'Meera',
  twin_009: 'Rohan',
  twin_010: 'Sneha',
  twin_011: 'Karthik',
  twin_012: 'Diya',
}

export const getTwinName = (twinId: string): string => {
  return twinNames[twinId] || twinId
}
