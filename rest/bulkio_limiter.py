"""
 Company: Geon Technologies, LLC
 Author: Josh Schindehette
 Copyright:
 (c) 2017 Geon Technologies, LLC. All rights reserved.
 Dissemination of this information or reproduction of this
 material is strictly prohibited unless prior written permission
 is obtained from Geon Technologies, LLC
"""
import math
import numpy
from ossie.utils.bulkio import bulkio_helpers
from bulkio import sri

def copy_sri(SRI):
    """
    This function copies the fields of an SRI object into a new object.
    """
    copied = sri.create()
    copied.hversion = SRI.hversion
    copied.xstart = SRI.xstart
    copied.xdelta = SRI.xdelta
    copied.xunits = SRI.xunits
    copied.subsize = SRI.subsize
    copied.ystart = SRI.ystart
    copied.ydelta = SRI.ydelta
    copied.yunits = SRI.yunits
    copied.mode = SRI.mode
    copied.streamID = SRI.streamID
    copied.blocking = SRI.blocking
    copied.keywords = SRI.keywords[:]
    return copied

def meanDownsampleX(dataMatrix, resampleFactor):
    """
    This function down-samples the matrix using a mean function across the X dimension.
    """
    # Initialize output matrix
    outMatrix = dataMatrix[:,::resampleFactor]
    # Calculate the dimensions to loop through
    numRows = outMatrix.shape[0]
    numCols = outMatrix.shape[1]
    origCols = dataMatrix.shape[1]
    # Loop through the rows
    for row in range(0, numRows):
        # Loop through the columns
        for col in range(0, numCols):
            # Check if there is an even (resampleFactor) amount of data to calculate a mean() on
            if ((col*resampleFactor+resampleFactor) > origCols):
                # Calculate the mean with whatever is left
                outMatrix[row, col] = dataMatrix[row, col*resampleFactor:].mean()
            else:
                # Calculate the mean with (resampleFactor) samples
                outMatrix[row, col] = dataMatrix[row, col*resampleFactor:col*resampleFactor+resampleFactor].mean()
    # Return output matrix
    return outMatrix

def meanDownsampleY(dataMatrix, resampleFactor):
    """
    This function down-samples the matrix using a mean function across the Y dimension.
    """
    # Initialize output matrix
    outMatrix = dataMatrix[::resampleFactor,:]
    # Calculate the dimensions to loop through
    numRows = outMatrix.shape[0]
    numCols = outMatrix.shape[1]
    origRows = dataMatrix.shape[0]
    # Loop through the columns
    for col in range(0, numCols):
        # Loop through the rows
        for row in range(0, numRows):
            # Check if there is an even (resampleFactor) amount of data to calculate a mean() on
            if ((row*resampleFactor+resampleFactor) > origRows):
                # Calculate the mean with whatever is left
                outMatrix[row, col] = dataMatrix[row*resampleFactor:, col].mean()
            else:
                # Calculate the mean with (resampleFactor) samples
                outMatrix[row, col] = dataMatrix[row*resampleFactor:row*resampleFactor+resampleFactor, col].mean()
    # Return output matrix
    return outMatrix

def limit(data, sri, xMax, xBegin=None, xEnd=None, xUseMean=True, yMax=None, yBegin=None, yEnd=None, yUseMean=True):
    """
    This function limits the output size of a bulkio packet.
    First, the data is sliced across two different dimensions (if applicable) with the indices (note the "inclusive" range definition):
        [xBegin, xEnd]
        [yBegin, yEnd]
    These indices are in terms of samples rather than data words. This means that xBegin=2 ignores two samples which
    is 4 words if the data is complex and 2 words if the data is scalar..
    Second, the data is down-sampled across two different dimensions (if applicable) to fit within the max sample sizes:
        xMax
        yMax
    The down-sampling is performed across the X dimension first (this only matters if the mean function is used).
    These max sample sizes are in terms of samples rather than data words. The down-sampling operation either drops
    samples or it uses the mean function to include information from the dropped samples.
    The following flags indicate which operation to use:
        xUseMean
        yUseMean
    """
    #============================================
    # Initialize
    #============================================
    outSRI = copy_sri(sri) # Copy SRI so it isn't modified in place
    sriChanged = False
    warningMessage = ""

    #============================================
    # Convert from a vector of words to a matrix of samples
    #============================================
    # Check if complex and convert (0:Scalar, 1:Complex)
    if (outSRI.mode == 1):
        outData = bulkio_helpers.bulkioComplexToPythonComplexList(data)
        # Divide by two since this parameter uses word indexing rather than sample indexing
        frameSize = outSRI.subsize/2
    else:
        outData = data
        frameSize = outSRI.subsize

    # Check for dimension (0:1D, otherwise:2D)
    if (outSRI.subsize == 0):
        xLength = len(outData)
        yLength = 1
    else:
        xLength = frameSize
        yLength = len(outData) / frameSize
        # Check that the frame size evenly fits in the data length
        if ((len(outData) % frameSize) > 0):
            # Warn and attempt to correct by slicing off the end of the packet
            warningMessage += "Malformed input packet!  Data with length=" + str(len(outData)) + " is not a multiple of the frame with length=" + str(frameSize) + "\n"
            adjustedLength = (int(len(outData)) / int(frameSize)) * frameSize
            outData = outData[:adjustedLength]
            warningMessage += "Dropped data to fix malformed input packet! Data now has length=" + str(adjustedLength) + "\n"

    # Convert to numpy array
    outData = numpy.array(outData)

    # Reshape data into matrix of yLength rows and xLength columns
    outData = outData.reshape((yLength, xLength))

    #============================================
    # Slice the data if necessary
    #============================================
    # Slice the end of the X axis first
    if (xEnd):
        # Check for valid xEnd
        if ((xEnd+1) <= xLength):
            # Slice (Use xEnd+1 since [xBegin, xEnd] range is inclusive)
            outData = outData[:,:xEnd+1]
            # Recalculate xLength - number of columns
            xLength = outData.shape[1]
        else:
            warningMessage += "Ignoring X axis end index! Index=" + str(xEnd) + " does not exist in samples with length=" + str(xLength)  + "\n"

    # Slice the beginning of the X axis second
    if (xBegin):
        # Check for valid xBegin
        if ((xBegin+1) <= xLength):
            # Slice
            outData = outData[:,xBegin:]
            # Recalculate xLength - number of columns
            xLength = outData.shape[1]
            # Modify SRI
            outSRI.xstart = outSRI.xstart + xBegin*outSRI.xunits
            # Check if the SRI was updated here
            if (sri.xstart != outSRI.xstart):
                sriChanged = True
        else:
            warningMessage += "Ignoring X axis beginning index! Index=" + str(xBegin) + " does not exist in samples with length=" + str(xLength)  + "\n"

    # Slice the end of the Y axis first
    if (yEnd):
        # Check for valid yEnd
        if ((yEnd+1) <= yLength):
            # Slice (Use yEnd+1 since [yBegin, yEnd] range is inclusive)
            outData = outData[:yEnd+1,:]
            # Recalculate yLength - number of rows
            yLength = outData.shape[0]
        else:
            warningMessage += "Ignoring Y axis end index! Index=" + str(yEnd) + " does not exist in samples with length=" + str(yLength)  + "\n"

    # Slice the beginning of the Y axis second
    if (yBegin):
        # Check for valid xBegin
        if ((yBegin+1) <= yLength):
            # Slice
            outData = outData[yBegin:,:]
            # Recalculate xLength - number of rows
            yLength = outData.shape[0]
            # Modify SRI
            outSRI.ystart = outSRI.ystart + yBegin*outSRI.yunits
            # Check if SRI was updated here
            if (sri.ystart != outSRI.ystart):
                sriChanged = True
        else:
            warningMessage += "Ignoring Y axis beginning index! Index=" + str(yBegin) + " does not exist in samples with length=" + str(yLength)  + "\n"

    #============================================
    # Down-sample the data if necessary
    #============================================
    # Check for down-sampling along the x axis
    xResampleFactor = 1
    if ((xMax) and (xMax < xLength)):
        # Calculate integer re-sample factor
        xResampleFactor = float(xLength) / float(xMax)
        xResampleFactor = int(math.ceil(xResampleFactor))
        # Down-sample
        if (xUseMean):
            # Use the average of the dropped samples and retained sample
            outData = meanDownsampleX(outData, xResampleFactor)
        else:
            # Drop samples when down-sampling
            outData = outData[:,::xResampleFactor]
        # Recalculate xLength - number of columns
        xLength = outData.shape[1]
        # Modify SRI
        outSRI.xdelta = outSRI.xdelta * xResampleFactor
        # The SRI was updated here since re-sampling was performed
        sriChanged = True

    # Update the subsize if this is two dimensional data
    if (outSRI.subsize > 0):
        outSRI.subsize = xLength
        # If this is complex data, use 2x multiplier since xLength is in
        # terms of samples whereas the subsize is in terms of words
        if (outSRI.mode == 1):
            outSRI.subsize = outSRI.subsize * 2
        # Check if the SRI was updated here
        if (sri.subsize != outSRI.subsize):
            sriChanged = True

    # Check for down-sampling along the y axis
    yResampleFactor = 1
    if ((yMax) and (yMax < yLength)):
        # Calculate integer re-sample factor
        yResampleFactor = float(yLength) / float(yMax)
        yResampleFactor = int(math.ceil(yResampleFactor))
        # Down-sample
        if (yUseMean):
            # Use the average of the dropped samples and retained sample
            outData = meanDownsampleY(outData, yResampleFactor)
        else:
            outData = outData[::yResampleFactor,:]
        # Recalculate yLength - number of rows
        yLength = outData.shape[0]
        # Modify SRI
        outSRI.ydelta = outSRI.ydelta * yResampleFactor
        # The SRI was updated here since re-sampling was performed
        sriChanged = True

    #============================================
    # Convert from a matrix of samples to a vector of words
    #============================================
    # Convert the matrix back to a list
    outData = outData.reshape((1, xLength*yLength)).squeeze().tolist()

    # Word-serialize the complex data
    if (outSRI.mode == 1):
        outData = bulkio_helpers.pythonComplexListToBulkioComplex(outData)

    return (outData, outSRI, xResampleFactor, yResampleFactor, sriChanged, warningMessage)
