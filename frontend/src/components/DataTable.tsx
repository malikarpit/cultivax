'use client';

interface DataTableProps {
  data: Record<string, any>[];
  columns: string[];
}

export default function DataTable({ data, columns }: DataTableProps) {
  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">No data available.</div>
    );
  }

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return '—';
    if (typeof value === 'boolean') return value ? '✅' : '❌';
    if (typeof value === 'object') return JSON.stringify(value);
    if (typeof value === 'string' && value.includes('T')) {
      try {
        return new Date(value).toLocaleDateString();
      } catch {
        return value;
      }
    }
    return String(value);
  };

  const formatHeader = (col: string): string => {
    return col
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse bg-white rounded-lg shadow-sm">
        <thead>
          <tr className="bg-gray-50 border-b">
            {columns.map((col) => (
              <th
                key={col}
                className="px-4 py-3 text-left text-sm font-medium text-gray-600"
              >
                {formatHeader(col)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIdx) => (
            <tr
              key={rowIdx}
              className="border-b hover:bg-gray-50 transition-colors"
            >
              {columns.map((col) => (
                <td key={col} className="px-4 py-3 text-sm text-gray-800">
                  {formatValue(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
