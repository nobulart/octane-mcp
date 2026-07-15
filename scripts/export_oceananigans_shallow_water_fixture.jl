#!/usr/bin/env julia
# Export a tiny real Oceananigans shallow-water state as CSV arrays.
#
# This script is intentionally small and deterministic. The Python wrapper
# `scripts/export_oceananigans_shallow_water_fixture.py` packages the CSV bundle
# into the committed `.npz` fixture consumed by the recipe adapter.
#
# Run directly:
#   julia --project=/Users/craig/src/Oceananigans.jl scripts/export_oceananigans_shallow_water_fixture.jl /tmp/ocean-csv

using DelimitedFiles
using Oceananigans
using Oceananigans.Grids: RectilinearGrid
using Oceananigans.Models: ShallowWaterModel
using Printf

outdir = length(ARGS) >= 1 ? ARGS[1] : error("usage: export_oceananigans_shallow_water_fixture.jl <output_dir>")
mkpath(outdir)

Nx = 24
Ny = 36
steps = 5
Δt = 0.02

grid = RectilinearGrid(size=(Nx, Ny), extent=(2, 2), topology=(Periodic, Periodic, Flat))
model = ShallowWaterModel(grid; gravitational_acceleration=9.81)
set!(model, h = (x, y) -> 1 + 0.05 * tanh(8 * (x - 1)), uh = 0.02, vh = 0.0)

for _ in 1:steps
    time_step!(model, Δt)
end

function as_2d(field)
    array = Array(interior(field))
    if ndims(array) == 3 && size(array, 3) == 1
        return dropdims(array; dims=3)
    end
    return array
end

h = as_2d(model.solution.h)
uh = as_2d(model.solution.uh)
vh = as_2d(model.solution.vh)

function center_x(field, nx, ny)
    if size(field, 1) == nx + 1
        return 0.5 .* (field[1:nx, 1:ny] .+ field[2:nx+1, 1:ny])
    elseif size(field, 1) == nx
        return field[1:nx, 1:ny]
    else
        error("unexpected x-staggered field shape $(size(field))")
    end
end

function center_y(field, nx, ny)
    if size(field, 2) == ny + 1
        return 0.5 .* (field[1:nx, 1:ny] .+ field[1:nx, 2:ny+1])
    elseif size(field, 2) == ny
        return field[1:nx, 1:ny]
    else
        error("unexpected y-staggered field shape $(size(field))")
    end
end

u = center_x(uh, Nx, Ny)
v = center_y(vh, Nx, Ny)

bathymetry = [-(0.9 + 0.28 * (i - 1) / max(Nx - 1, 1) + 0.08 * sin(2π * (j - 1) / Ny)) for i in 1:Nx, j in 1:Ny]

writedlm(joinpath(outdir, "eta.csv"), h, ',')
writedlm(joinpath(outdir, "u.csv"), u, ',')
writedlm(joinpath(outdir, "v.csv"), v, ',')
writedlm(joinpath(outdir, "bathymetry.csv"), bathymetry, ',')

open(joinpath(outdir, "metadata.txt"), "w") do io
    println(io, "source_library=Oceananigans.jl")
    println(io, "exporter=export_oceananigans_shallow_water_fixture.jl")
    println(io, "grid_shape=$(Nx)x$(Ny)")
    println(io, "time_steps=$(steps)")
    println(io, "dt_seconds=$(Δt)")
    println(io, "field_names=eta,u,v,bathymetry")
    println(io, "model=ShallowWaterModel")
    @printf(io, "eta_min=%.12f\n", minimum(h))
    @printf(io, "eta_max=%.12f\n", maximum(h))
    @printf(io, "u_max=%.12f\n", maximum(abs.(u)))
    @printf(io, "v_max=%.12f\n", maximum(abs.(v)))
end

@printf("oceananigans_export_ok output=%s grid=%dx%d eta_min=%.6f eta_max=%.6f u_max=%.6f v_max=%.6f\n",
        outdir, Nx, Ny, minimum(h), maximum(h), maximum(abs.(u)), maximum(abs.(v)))
