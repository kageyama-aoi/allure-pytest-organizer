export default {
  name: "ファイル整理ツールのテスト結果",
  output: "./allure-report",
  plugins: {
    awesome: {
      options: {
        reportName: "ファイル整理ツールのテスト結果",
        // 一覧を「ファイル名 → クラス名」ではなく、テストコードに書いた日本語の分類
        // （epic → feature → story）の順に並べる
        groupBy: ["epic", "feature", "story"],
      },
    },
  },
};
