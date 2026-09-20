export function formatCurrency(amount: number | null | undefined, currency: string = 'INR'): string {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return '—';
  }
  
  const curr = (currency || 'INR').toUpperCase();
  
  try {
    if (curr === 'INR') {
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
      }).format(amount);
    }
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: curr,
      maximumFractionDigits: 0
    }).format(amount);
  } catch (e) {
    return `₹${amount.toLocaleString('en-IN')}`;
  }
}
