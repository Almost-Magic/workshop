import{j as r}from"./index-CWZPIZYX.js";import{m as c}from"./ui-f0mybGUZ.js";const d={primary:"bg-sage text-white hover:bg-sage-dark active:bg-sage-dark",secondary:"bg-warmGray-100 text-warmGray-800 hover:bg-warmGray-200 dark:bg-warmGray-800 dark:text-warmGray-100 dark:hover:bg-warmGray-700",danger:"bg-red-500 text-white hover:bg-red-600 active:bg-red-600",ghost:"bg-transparent text-warmGray-600 hover:bg-warmGray-100 dark:text-warmGray-400 dark:hover:bg-warmGray-800"},g={sm:"px-3 py-1.5 text-sm",md:"px-4 py-2 text-base",lg:"px-6 py-3 text-lg"},w=({variant:t="primary",size:s="md",children:o,disabled:i,loading:a,fullWidth:n,className:l="",...m})=>{const e=i||a;return r.jsxs(c.button,{whileHover:{scale:e?1:1.02},whileTap:{scale:e?1:.98},className:`
        inline-flex items-center justify-center font-medium rounded-lg
        transition-colors duration-150 ease-in-out
        focus:outline-none focus:ring-2 focus:ring-sage focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed
        ${d[t]}
        ${g[s]}
        ${n?"w-full":""}
        ${l}
      `,disabled:e,...m,children:[a&&r.jsxs("svg",{className:"animate-spin -ml-1 mr-2 h-4 w-4",xmlns:"http://www.w3.org/2000/svg",fill:"none",viewBox:"0 0 24 24",children:[r.jsx("circle",{className:"opacity-25",cx:"12",cy:"12",r:"10",stroke:"currentColor",strokeWidth:"4"}),r.jsx("path",{className:"opacity-75",fill:"currentColor",d:"M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"})]}),o]})};export{w as B};
