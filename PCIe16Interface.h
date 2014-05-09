/*! \file Interface.h
 *  \brief Exported functions for Interface.dll
 *  \author Anna Linnenberger (alinnenberger@bnonlinear.com)
 *  \author Dane Elshof (dane@bnonlinear.com)
 *  \date February 2012
 *
 *  Exported functions for Interface.dll, a DLL for interfacing
 *  with BNS PCIe 16-bit 512 and 256 SLM hardware.
 *
 */

/* --- Settings Enumerations								--- */
/*! \brief An enum for representing liquid crystal types.
 */
enum LC_TYPE { FERROELECTRIC = 0, NEMATIC = 1};
typedef enum LC_TYPE LC_TYPE;
/*! \brief An enum for representing 2D calibration image types.
 */
enum CAL_TYPE { NUC = 0, WFC = 1 };
typedef enum CAL_TYPE CAL_TYPE;
/*! \brief An enum for representing temperature units.
 */
enum TEMPUNITS {CELSIUS = 0, FAHRENHEIT = 1 };
typedef enum TEMPUNITS TEMPUNITS;

/* --- Hardware Initialization								--- */
/*! \brief Opens all available PCIe 16-bit SLM controllers and returns the number of boards available
 */
extern "C" __declspec(dllexport) int    Constructor			(LC_TYPE LCType);
/*! \brief Closes all PCIe 16-bit SLM Controllers that were opened with Constructor
 */
extern "C" __declspec(dllexport) void   Deconstructor		();

/* --- Image File Loading									--- */
extern "C" __declspec(dllexport) void   ReadTIFF			(const char* FilePath, unsigned short* ImageData, unsigned int ScaleWidth, unsigned int ScaleHeight);
extern "C" __declspec(dllexport) void	GetTIFFInfo			(const char* FilePath, unsigned int* Width, unsigned int* Height, unsigned short* BPP);

/* --- On-the-fly Image Loading								--- */
extern "C" __declspec(dllexport) void   WriteImage			(int Board, unsigned short* Image);

/* --- Interrupt-timed Image Sequencing						--- */
extern "C" __declspec(dllexport) void   LoadSequence		(int Board, unsigned short* Images, int NumberOfImages);
extern "C" __declspec(dllexport) void   SetSequencingRate	(double FrameRate);
extern "C" __declspec(dllexport) void   StartSequence		();
extern "C" __declspec(dllexport) int    GetCurSeqImage		(int Board);
extern "C" __declspec(dllexport) void   StopSequence		();

/* --- Hardware Settings and Information					--- */
extern "C" __declspec(dllexport) int    GetImageSize		(int Board);
extern "C" __declspec(dllexport) bool   GetSLMPower			(int Board);
extern "C" __declspec(dllexport) void   SLMPower			(int Board, bool PowerOn);
extern "C" __declspec(dllexport) void   WriteCal			(int Board, CAL_TYPE CalType, unsigned short* Image);
extern "C" __declspec(dllexport) void   LoadLUTFile			(int Board, char* LUTPath);
extern "C" __declspec(dllexport) int    ComputeTF			(float FrameRate);
extern "C" __declspec(dllexport) void   SetTrueFrames		(int Board, int TrueFrames);
extern "C" __declspec(dllexport) double GetInternalTemp		(int Board, TEMPUNITS units);
