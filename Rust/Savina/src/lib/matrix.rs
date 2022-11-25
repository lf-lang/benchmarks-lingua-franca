/*
 * Copyright (c) 2021, TU Dresden.
 *
 * Redistribution and use in source and binary forms, with or without modification,
 * are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
 * THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
 * THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * @author Johannes Hayeß
 */
#![allow(dead_code)]

use std::ops::Add;
use std::fmt;

#[derive(Debug, Clone)]
pub struct Matrix<T> {
    data: Vec<T>,
    size_x: usize,
    size_y: usize,
}

pub struct TransposedMatrix<T>(Matrix<T>);

impl<T> Matrix<T> {
    pub fn new(size_x: usize, size_y: usize) -> Self where T: Default + Clone {
        Matrix::<T> {
            data: vec![T::default(); size_x * size_y],
            size_x,
            size_y,
        }
    }

    pub fn get(&self, x: usize, y: usize) -> &T {
        &self.data[x * self.size_y + y]
    }

    pub fn set(&mut self, x: usize, y: usize, value: T) {
        self.data[x * self.size_y + y] = value;
    }
}

pub fn matrix_sum<T>(matrices: &[Matrix<T>]) -> Matrix<T>
    where
        T: Default + Clone + Copy + Add<Output=T>,
{
    let size_x = matrices[0].size_x;
    let size_y = matrices[0].size_y;
    let mut result = Matrix::<T>::new(size_x, size_y);
    for x in 0..size_x {
        for y in 0..size_y {
            for m in matrices {
                result.set(x, y, *result.get(x, y) + *m.get(x, y))
            }
        }
    }

    result
}

impl<T> TransposedMatrix<T> {
    pub fn new(size_x: usize, size_y: usize) -> Self where T: Default + Clone {
        Self(Matrix::new(size_y, size_x))
    }

    pub fn get(&self, x: usize, y: usize) -> &T {
        self.0.get(y, x)
    }

    pub fn set(&mut self, x: usize, y: usize, value: T) {
        self.0.set(y, x, value)
    }
}

impl<T: fmt::Display> fmt::Display for Matrix<T> {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        for i in 0..self.size_x {
            for j in 0..self.size_y {
                write!(f, "{} ", self.get(i, j))?;
            }
            write!(f, "\n")?;
        }
        Ok(())
    }
}

impl<T: fmt::Display> fmt::Display for TransposedMatrix<T> {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}
