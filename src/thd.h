/*****************************************************************************
   Major portions of this software are copyrighted by the Medical College
   of Wisconsin, 1994-2000, and are released under the Gnu General Public
   License, Version 2.  See the file README.Copyright for details.
******************************************************************************/
   
#ifndef _MCW_THDSOURCE_HEADER_
#define _MCW_THDSOURCE_HEADER_

#define THD_FATAL_ERROR(str) \
  { fprintf(stderr,"\a\n*** FATAL INTERAL ERROR: %s\n",str);sleep(1);exit(-1); }

#define ATR_ALLINC 8

#define DSET_ERR(str) \
   {fprintf(stderr,"\n*** DATASET error:   %s\n",str);dset_ok=False;}

#define DSET_WARN(str) \
   {fprintf(stderr,"\n*** DATASET warning: %s\n",str);}

#define WRITE_ERR(str) \
  { fprintf(stderr,"*** Datablock write error: %s\n",str); return False; }

#define ORCODE(aa) \
  ( (aa)=='R' ? ORI_R2L_TYPE : (aa)=='L' ? ORI_L2R_TYPE : \
    (aa)=='P' ? ORI_P2A_TYPE : (aa)=='A' ? ORI_A2P_TYPE : \
    (aa)=='I' ? ORI_I2S_TYPE : (aa)=='S' ? ORI_S2I_TYPE : ILLEGAL_TYPE )

#define OR3OK(x,y,z) ( ((x)&6) + ((y)&6) + ((z)&6) == 6 )

#define XLAB(xl,xv) ((xl) = ((xv)==0.0) ? (ZZ) : ( ((xv)<0.0) ? (RR) : (LL) ))
#define YLAB(yl,yv) ((yl) = ((yv)==0.0) ? (ZZ) : ( ((yv)<0.0) ? (AA) : (PP) ))
#define ZLAB(zl,zv) ((zl) = ((zv)==0.0) ? (ZZ) : ( ((zv)<0.0) ? (II) : (SS) ))

#define FSWAP(x,y) (tf=(x),(x)=(y),(y)=tf)

#include "mcw_malloc.h"

#endif
