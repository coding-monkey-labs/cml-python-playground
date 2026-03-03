import { DataFrame, Transform } from '../types';

export function applyTransforms(data: DataFrame[], transforms: Transform[]): DataFrame[] {
  let result = data;

  for (const transform of transforms) {
    switch (transform.type) {
      case 'filter':
        result = applyFilter(result, transform.options);
        break;
      case 'groupBy':
        result = applyGroupBy(result, transform.options);
        break;
      case 'sortBy':
        result = applySortBy(result, transform.options);
        break;
      case 'calculateField':
        result = applyCalculateField(result, transform.options);
        break;
      case 'organize':
        result = applyOrganize(result, transform.options);
        break;
      case 'reduce':
        result = applyReduce(result, transform.options);
        break;
    }
  }

  return result;
}

function applyFilter(data: DataFrame[], options: Record<string, unknown>): DataFrame[] {
  const fieldName = options.field as string;
  const operator = options.operator as string;
  const value = options.value as number | string;

  return data.map(frame => {
    const fieldIndex = frame.fields.findIndex(f => f.name === fieldName);
    if (fieldIndex === -1) return frame;

    const field = frame.fields[fieldIndex];
    const mask = field.values.map(v => {
      switch (operator) {
        case 'eq': return v === value;
        case 'neq': return v !== value;
        case 'gt': return (v as number) > (value as number);
        case 'lt': return (v as number) < (value as number);
        case 'gte': return (v as number) >= (value as number);
        case 'lte': return (v as number) <= (value as number);
        case 'contains': return String(v).includes(String(value));
        default: return true;
      }
    });

    return {
      ...frame,
      length: mask.filter(Boolean).length,
      fields: frame.fields.map(f => ({
        ...f,
        values: f.values.filter((_, i) => mask[i]),
      })),
    };
  });
}

function applyGroupBy(data: DataFrame[], _options: Record<string, unknown>): DataFrame[] {
  // Simplified group-by: just passes through for now
  return data;
}

function applySortBy(data: DataFrame[], options: Record<string, unknown>): DataFrame[] {
  const fieldName = options.field as string;
  const desc = options.desc as boolean ?? false;

  return data.map(frame => {
    const fieldIndex = frame.fields.findIndex(f => f.name === fieldName);
    if (fieldIndex === -1) return frame;

    const indices = Array.from({ length: frame.length }, (_, i) => i);
    indices.sort((a, b) => {
      const va = frame.fields[fieldIndex].values[a];
      const vb = frame.fields[fieldIndex].values[b];
      if (va === vb) return 0;
      const cmp = (va as number) < (vb as number) ? -1 : 1;
      return desc ? -cmp : cmp;
    });

    return {
      ...frame,
      fields: frame.fields.map(f => ({
        ...f,
        values: indices.map(i => f.values[i]),
      })),
    };
  });
}

function applyCalculateField(data: DataFrame[], options: Record<string, unknown>): DataFrame[] {
  const alias = options.alias as string || 'Calculated';
  const operation = options.operation as string;
  const fieldA = options.fieldA as string;
  const fieldB = options.fieldB as string;

  return data.map(frame => {
    const a = frame.fields.find(f => f.name === fieldA);
    const b = frame.fields.find(f => f.name === fieldB);
    if (!a || !b) return frame;

    const values = a.values.map((va, i) => {
      const numA = va as number;
      const numB = b.values[i] as number;
      switch (operation) {
        case 'add': return numA + numB;
        case 'subtract': return numA - numB;
        case 'multiply': return numA * numB;
        case 'divide': return numB !== 0 ? numA / numB : 0;
        default: return numA;
      }
    });

    return {
      ...frame,
      fields: [...frame.fields, { name: alias, type: 'number' as const, values }],
    };
  });
}

function applyOrganize(data: DataFrame[], options: Record<string, unknown>): DataFrame[] {
  const excludeFields = options.exclude as string[] || [];
  const renameMap = options.rename as Record<string, string> || {};

  return data.map(frame => ({
    ...frame,
    fields: frame.fields
      .filter(f => !excludeFields.includes(f.name))
      .map(f => ({
        ...f,
        name: renameMap[f.name] || f.name,
      })),
  }));
}

function applyReduce(data: DataFrame[], options: Record<string, unknown>): DataFrame[] {
  const reducer = options.reducer as string || 'mean';

  return data.map(frame => ({
    ...frame,
    length: 1,
    fields: frame.fields.map(f => {
      if (f.type !== 'number') return { ...f, values: [f.values[0]] };

      const nums = f.values as number[];
      let reduced: number;
      switch (reducer) {
        case 'sum': reduced = nums.reduce((a, b) => a + b, 0); break;
        case 'mean': reduced = nums.reduce((a, b) => a + b, 0) / nums.length; break;
        case 'min': reduced = Math.min(...nums); break;
        case 'max': reduced = Math.max(...nums); break;
        case 'count': reduced = nums.length; break;
        case 'last': reduced = nums[nums.length - 1]; break;
        case 'first': reduced = nums[0]; break;
        default: reduced = nums.reduce((a, b) => a + b, 0) / nums.length;
      }
      return { ...f, values: [Math.round(reduced * 100) / 100] };
    }),
  }));
}
