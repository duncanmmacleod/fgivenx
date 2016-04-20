""" This script computes the grid for contours of a function
    reconstruction plot.

    If one has
     * independent variable x
     * dependent variable y
     * functional form y = f(x,theta) parameterised by theta

    Assuming that you have obtained samples of theta from an MCMC
    process, we aim to compute:

                  /
    P( y | x ) =  | P( y = f(x,theta) | x, theta ) dtheta ,  (1)
                  /

    which gives our degree of knowledge for each y value given an x value.

    In fact, for a more representative plot, we are not actually
    interested in the value of the probability density (1), but in fact
    require the "iso-probablity posterior mass:"

                        /
    m( y | x ) =        | P(y'|x) dy'
                        /
                P(y'|x) < P(y|x)

    We thus need to compute this function on a rectangular grid of x and y's

    Any questions, please email Will Handley <wh260@mrao.cam.ac.uk>
"""
import pickle
import numpy
import matplotlib.pyplot
import scipy

from fgivenx.utils import PMF
from fgivenx.progress_bar import pbar

def load_contours(datafile):
    """ Load contours from file. """
    return pickle.load(open(datafile, 'r'))

class Contours(object):
    """ Calculate and plot contours.

        Parameters
        ----------
        posterior: FunctionPosterior
            set of equally weighted functional posterior samples.
        xrange: tuple(float,float)
            minimum and maximum of independent variable.
        nx: int, optional
            (Default: 200)
            Number of bins in x.
        ny: int, optional
            (Default: nx)
            Number of bins in y.
    """

    def __init__(self, posterior, x_range, nx=200, ny='nx'):

        if ny == 'nx':
            ny = nx

        # Set up x coordinates
        self.x = numpy.linspace(x_range[0], x_range[1], nx)

        # Compute masses at each value of x
        masses = [PMF(posterior(x)) for x in pbar(self.x, desc="computing masses")]

        # Compute upper and lower bounds on y
        self.upper = max([m.upper for m in masses])
        self.lower = min([m.lower for m in masses])

        # Set up y coordinates
        self.y = numpy.linspace(self.lower, self.upper, ny)

        # Compute densities across the grid
        self.z = [[m(y) for m in masses] for y in self.y]

        self.cbar = None


    def save(self, datafile):
        """ Save contours to file """
        pickle.dump(self, open(datafile, 'w'))
        return self

    def plot(self, ax,
             colors=matplotlib.pyplot.cm.Reds_r,
             smooth=False,
             contour_line_levels='[1,2]',
             linewidths=1.0,
             contour_color_levels='numpy.arange(0, contour_line_levels[-1] + 1, fineness)',
             fineness=0.5):
        """ Plot computed contours.

            Parameters
            ----------
            ax: matplotlib.axes._subplots.AxesSubplot
                Axes to plot the contours onto.
                Typically generated with:
                    fig, ax = matplotlib.pyplot.subplots()

            colours: matplotlib.colors.LinearSegmentedColormap, optional
                (Default: matplotlib.pyplot.cm.Reds_r)
                Color scheme to plot with. Recommend plotting in reverse
            smooth: bool, optional
                (Default: False)
                Whether to smooth the contours.
            contour_line_levels: List[float], optional
                (Default: [1,2])
                Contour lines to be plotted.
            linewidth: float, optional
                (Default: 0.1)
                Thickness of contour lines
            contour_color_levels: List[float], optional
                (Default: numpy.arange(0, contour_line_levels[-1] + 1, fineness))
                Contour color levels.
            fineness: float, optional
                (Default: 0.1)
                Spacing of contour color levels.



            Returns
            -------
            cbar: matplotlib.contour.QuadContourSet
                Colours to create a global colour bar

            Functionality mostly determined by modifications to ax
        """

        # define the default contour lines as 1,2
        if contour_line_levels == '[1,2]':
            contour_line_levels = [1, 2]

        # Set up the fine contour gradation as 1 sigma above the levels above,
        # and with specified fineness
        if contour_color_levels == 'numpy.arange(0, contour_line_levels[-1] + 1, fineness)':
            contour_color_levels = numpy.arange(0, contour_line_levels[-1] + 1, fineness)

        # Create numpy arrays
        x = numpy.array(self.x)
        y = numpy.array(self.y)
        z = numpy.array(self.z)

        # Convert to sigmas
        z = numpy.sqrt(2) * scipy.special.erfinv(1 - z)

        # Gaussian filter if desired the sigmas by a factor of 1%
        if smooth:
            z = scipy.ndimage.gaussian_filter(z, sigma=numpy.array(z.shape) / 100.0, order=0)

        # Plot the filled contours onto the axis ax
        cbar = ax.contourf(x, y, z, cmap=colors, levels=contour_color_levels)

        # Plot some sigma-based contour lines
        ax.contour(x, y, z, colors='k', linewidths=linewidths, levels=contour_line_levels)

        # Set limits on axes
        ax.set_xlim([min(x), max(x)])
        ax.set_ylim([min(y), max(y)])

        # Return the contours for use as a colourbar later
        return cbar
