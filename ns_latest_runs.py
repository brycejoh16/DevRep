from input_deck import inputs

C=[   inputs(nb_loops=100000,
         nb_steps=5,
         mutation_type='dynamic',
         nb_mutations=12,
         nb_snapshots=50,
         Nb_sequences=10000,
         yield2optimize='Developability',
         nb_cores=8), # 22752495
    inputs(nb_loops=50000,
         nb_steps=5,
         mutation_type='dynamic',
         nb_mutations=12,
         nb_snapshots=50,
         Nb_sequences=100000,
         yield2optimize='Developability',
         nb_cores=32), # 22752711
inputs(nb_loops=100000,
         nb_steps=5,
         mutation_type='dynamic',
         nb_mutations=12,
         nb_snapshots=50,
         Nb_sequences=10000,
         yield2optimize='SH_Average_bc',
         nb_cores=8), #22752567
inputs(nb_loops=100000,
         nb_steps=5,
         mutation_type='dynamic',
         nb_mutations=12,
         nb_snapshots=50,
         Nb_sequences=10000,
         yield2optimize='IQ_Average_bc',
         nb_cores=8),# 22752649

   ]