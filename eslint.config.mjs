import next from 'eslint-config-next';

export default [
  ...next,
  {
    ignores: ['concept/**', 'references/**', '.claude/**', 'sergey playground/**', 'analysis/**'],
  },
];
