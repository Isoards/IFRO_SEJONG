// Performance optimization configuration
const path = require("path");

module.exports = {
  webpack: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      "@shared": path.resolve(__dirname, "src/shared"),
      "@features": path.resolve(__dirname, "src/features"),
      "@components": path.resolve(__dirname, "src/shared/components"),
      "@services": path.resolve(__dirname, "src/shared/services"),
      "@utils": path.resolve(__dirname, "src/shared/utils"),
      "@types": path.resolve(__dirname, "src/shared/types"),
      "@constants": path.resolve(__dirname, "src/shared/constants"),
    },
    optimization: {
      splitChunks: {
        chunks: "all",
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: "vendors",
            chunks: "all",
          },
          features: {
            test: /[\\/]src[\\/]features[\\/]/,
            name: "features",
            chunks: "all",
            minChunks: 2,
          },
          shared: {
            test: /[\\/]src[\\/]shared[\\/]/,
            name: "shared",
            chunks: "all",
            minChunks: 2,
          },
        },
      },
    },
  },
};
