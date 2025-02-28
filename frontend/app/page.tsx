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
          bgcolor:'#383838',
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
          sx={{color:'#fff',bgcolor:'#1c1c1c'}}
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
          bgcolor:'#383838',
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
          sx={{color:'#fff',bgcolor:'#1c1c1c'}}
        >
          Chat
        </Button>

      </Box>

    </Box>
  );
}
