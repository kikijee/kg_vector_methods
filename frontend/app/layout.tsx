import { AppRouterCacheProvider } from '@mui/material-nextjs/v15-appRouter';
import { ThemeProvider } from '@mui/material/styles';
import { theme } from './theme/theme';

 export default function RootLayout(props: any) {
   const { children } = props;
   return (
     <html lang="en">
      <body>
            <AppRouterCacheProvider>
            <ThemeProvider theme={theme}>
                {children}
            </ThemeProvider>
            </AppRouterCacheProvider>
       </body>
     </html>
   );
 }
