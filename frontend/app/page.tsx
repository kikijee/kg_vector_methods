import { Box, Typography, CssBaseline, Button } from "@mui/material";

export default function Home() {
  return (
    <Box
      sx={{
        display:'flex',
        minHeight:'100vh',
        justifyContent:'center',
        alignItems:'center',
        gap:5
      }}
    >
      <CssBaseline/>

      <Box
        sx={{
          display:'flex',
          flexDirection:'column',
          justifyContent:'center',
          alignItems:'center',
          width:500,
          height:500,
          bgcolor:'#7a7a7a',
          borderRadius:5,
          gap:5
        }}
      >
        <Typography
          sx={{
            fontSize:20
          }}
        >
          Upload Files
        </Typography>

        <Button 
          variant="contained"
        >
          Upload
        </Button>

      </Box>

      <Box
        sx={{
          display:'flex',
          flexDirection:'column',
          justifyContent:'center',
          alignItems:'center',
          width:500,
          height:500,
          bgcolor:'#7a7a7a',
          borderRadius:5,
          gap:5
        }}
      >
        <Typography
          sx={{
            fontSize:20
          }}
        >
          Chat With Bot
        </Typography>

        <Button 
          variant="contained"
          href="/chat"
        >
          Chat
        </Button>

      </Box>

    </Box>
  );
}
