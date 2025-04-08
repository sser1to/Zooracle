using System.ComponentModel.DataAnnotations.Schema;
using System.ComponentModel.DataAnnotations;

namespace backend.Models
{
    public class favorite_animals
    {
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int id { get; set; }
        public int? user_id { get; set; }
        [ForeignKey("user_id")]
        public users user { get; set; }

        public int? animal_id { get; set; }
        [ForeignKey("animal_id")]
        public animals animal { get; set; }
    }
}
